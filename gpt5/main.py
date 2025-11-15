import time
import json
from typing import List, Dict, Any, Optional, Tuple
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from tqdm import tqdm
from sklearn.feature_extraction.text import CountVectorizer

HH_API = "https://api.hh.ru"
HEADERS = {
    # укажите свой контакт, чтобы hh мог связаться при необходимости
    "User-Agent": "HH-Analytics/1.0 (your_email@example.com)"
}


# -------------------------- СЕТЕВЫЕ ХЕЛПЕРЫ --------------------------

def hh_get(url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 5, base_sleep: float = 1.0) -> Dict[
    str, Any]:
    """
    Безопасный GET с бэкоффом, учитывает 429/5xx и сетевые ошибки.
    """
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
            if r.status_code == 429:
                # Превышен лимит — ждём из заголовка или экспоненциально
                reset = r.headers.get("X-RateLimit-Reset")
                if reset:
                    sleep_s = float(reset)
                else:
                    sleep_s = base_sleep * (2 ** attempt)
                time.sleep(sleep_s)
                continue
            if 500 <= r.status_code < 600:
                time.sleep(base_sleep * (2 ** attempt))
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(base_sleep * (2 ** attempt))
    raise RuntimeError(f"Failed to GET {url} after {max_retries} retries")


# -------------------------- ПОИСК РЕГИОНА --------------------------

def get_all_areas_flat() -> pd.DataFrame:
    """
    Возвращает плоскую таблицу со всеми регионами/городами hh (id, name, parent_name).
    """
    data = hh_get(f"{HH_API}/areas")
    rows = []

    def walk(node, parent=None, country=None):
        name = node.get("name")
        node_id = node.get("id")
        if parent is None:
            country = name
        rows.append({
            "id": node_id,
            "name": name,
            "parent": parent,
            "country": country
        })
        for ch in node.get("areas", []):
            walk(ch, parent=name, country=country)

    for country in data:
        walk(country, parent=None, country=country.get("name"))
    return pd.DataFrame(rows)


def find_area_id(query: str) -> Optional[str]:
    """
    Находит id региона/города по подстроке (без регистра).
    Возвращает первый матч.
    """
    areas = get_all_areas_flat()
    q = query.casefold()
    matches = areas[areas["name"].str.casefold().str.contains(q)]
    if len(matches) == 0:
        return None
    return str(matches.iloc[0]["id"])


# -------------------------- ПОИСК ВАКАНСИЙ --------------------------

def search_vacancy_ids(
        text: Optional[str] = None,
        area_id: Optional[str] = None,
        professional_role_ids: Optional[List[int]] = None,
        period_days: int = 30,
        per_page: int = 100,
        max_pages: Optional[int] = None,
        max_results: Optional[int] = None
) -> List[str]:
    """
    Возвращает список id вакансий по критериям.
    period_days: вакансии за последние N дней (1..30).
    """
    params = {
        "page": 0,
        "per_page": per_page,
        "period": period_days,
    }
    if text:
        # ищем в названии вакансии
        params["text"] = text
        params["search_field"] = "name"
    if area_id:
        params["area"] = area_id
    if professional_role_ids:
        # список id профессиональных ролей (через запятую)
        params["professional_role"] = ",".join(map(str, professional_role_ids))

    ids = []
    page = 0
    pbar = None
    while True:
        params["page"] = page
        data = hh_get(f"{HH_API}/vacancies", params=params)
        items = data.get("items", [])
        if pbar is None:
            # прогресс по общему числу страниц
            total_pages = data.get("pages", 0)
            if max_pages is not None:
                total_pages = min(total_pages, max_pages)
            pbar = tqdm(total=total_pages, desc="Поиск страниц", unit="page")

        ids.extend([it["id"] for it in items])

        page += 1
        pbar.update(1)

        if max_pages is not None and page >= max_pages:
            break

        if page >= data.get("pages", 0):
            break

        if max_results is not None and len(ids) >= max_results:
            ids = ids[:max_results]
            break

        time.sleep(0.2)  # щадим API

    if pbar:
        pbar.close()
    # уникализируем
    ids = list(dict.fromkeys(ids))
    return ids


# -------------------------- ДЕТАЛИ ВАКАНСИЙ --------------------------

def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    return soup.get_text(separator=" ").strip()


def fetch_vacancy_detail(vac_id: str) -> Dict[str, Any]:
    data = hh_get(f"{HH_API}/vacancies/{vac_id}")
    # нормализуем полезные поля
    key_skills = [ks.get("name", "").strip() for ks in data.get("key_skills", []) if ks.get("name")]
    description_text = html_to_text(data.get("description", "") or "")
    snippet = data.get("snippet") or {}
    requirement = snippet.get("requirement") or ""
    responsibility = snippet.get("responsibility") or ""

    salary = data.get("salary") or {}
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "area": (data.get("area") or {}).get("name"),
        "employer": (data.get("employer") or {}).get("name"),
        "published_at": data.get("published_at"),
        "experience": (data.get("experience") or {}).get("name"),
        "employment": (data.get("employment") or {}).get("name"),
        "schedule": (data.get("schedule") or {}).get("name"),
        "salary_from": salary.get("from"),
        "salary_to": salary.get("to"),
        "salary_currency": salary.get("currency"),
        "key_skills": key_skills,
        "requirement": requirement,
        "responsibility": responsibility,
        "description": description_text,
        "url": data.get("alternate_url") or data.get("url"),
        "professional_roles": [pr.get("name") for pr in data.get("professional_roles", []) if pr.get("name")],
    }


def fetch_vacancies_details(ids: List[str]) -> List[Dict[str, Any]]:
    details = []
    for vid in tqdm(ids, desc="Загрузка вакансий", unit="vac"):
        try:
            details.append(fetch_vacancy_detail(vid))
        except Exception as e:
            # логируем и продолжаем
            print(f"warn: skip {vid}: {e}")
        time.sleep(0.2)  # щадим API
    return details


# -------------------------- АГРЕГАЦИЯ --------------------------

def top_ngrams(
        texts: List[str],
        ngram_range: Tuple[int, int] = (1, 2),
        top_k: int = 30,
        min_df: int = 2
) -> List[Tuple[str, int]]:
    """
    Возвращает топ n-грамм с частотами для русскоязычных текстов.
    """
    texts = [t for t in (texts or []) if isinstance(t, str) and t.strip()]
    if not texts:
        return []
    vec = CountVectorizer(
        stop_words="russian",
        ngram_range=ngram_range,
        lowercase=True,
        min_df=min_df
    )
    X = vec.fit_transform(texts)
    freqs = np.asarray(X.sum(axis=0)).ravel()
    terms = np.array(vec.get_feature_names_out())
    order = np.argsort(-freqs)
    top_idx = order[:top_k]
    return list(zip(terms[top_idx], freqs[top_idx].astype(int)))


def aggregate(df: pd.DataFrame, top_k: int = 30) -> Dict[str, Any]:
    # Топ ключевых навыков
    skills = (
        df["key_skills"]
        .explode()
        .dropna()
        .str.strip()
        .str.lower()
        .value_counts()
    )

    # Требования и задачи (ответственности) — извлекаем n-граммы
    requirements_texts = df["requirement"].fillna("").astype(str).tolist()
    responsibilities_texts = df["responsibility"].fillna("").astype(str).tolist()

    top_req = top_ngrams(requirements_texts, ngram_range=(1, 3), top_k=top_k, min_df=2)
    top_resp = top_ngrams(responsibilities_texts, ngram_range=(1, 3), top_k=top_k, min_df=2)

    # Ко-встречаемость навыков (простая)
    from sklearn.preprocessing import MultiLabelBinarizer
    mlb = MultiLabelBinarizer()
    skill_matrix = mlb.fit_transform(df["key_skills"])
    skill_names = [s.lower() for s in mlb.classes_]
    cooc = (skill_matrix.T @ skill_matrix)  # квадратная матрица
    np.fill_diagonal(cooc, 0)
    # Топ пар по ко-встречаемости
    pairs = []
    for i in range(cooc.shape[0]):
        for j in range(i + 1, cooc.shape[1]):
            c = int(cooc[i, j])
            if c > 0:
                pairs.append(((skill_names[i], skill_names[j]), c))
    pairs.sort(key=lambda x: -x[1])
    top_skill_pairs = pairs[:top_k]

    return {
        "skills_counts": skills,
        "top_requirements_ngrams": top_req,
        "top_responsibilities_ngrams": top_resp,
        "top_skill_pairs": top_skill_pairs
    }


# -------------------------- PIPELINE / MAIN --------------------------

def run_pipeline(
        query_text: str,
        area_query_or_id: Optional[str] = None,
        professional_role_ids: Optional[List[int]] = None,
        period_days: int = 30,
        per_page: int = 100,
        max_pages: Optional[int] = None,
        max_results: Optional[int] = None,
        save_prefix: str = "hh_result",
) -> Dict[str, Any]:
    """
    Основной сценарий:
    - ищет id вакансий,
    - загружает детали,
    - сохраняет сырые данные,
    - строит агрегаты и сохраняет их.
    """
    # Определим area_id (если передана строка)
    area_id = None
    if area_query_or_id:
        if area_query_or_id.isdigit():
            area_id = area_query_or_id
        else:
            area_id = find_area_id(area_query_or_id)
            if area_id is None:
                print(f"Не найден регион по '{area_query_or_id}', продолжаю без фильтра региона.")

    ids = search_vacancy_ids(
        text=query_text,
        area_id=area_id,
        professional_role_ids=professional_role_ids,
        period_days=period_days,
        per_page=per_page,
        max_pages=max_pages,
        max_results=max_results
    )
    print(f"Найдено id вакансий: {len(ids)}")

    details = fetch_vacancies_details(ids)
    print(f"Загружено вакансий: {len(details)}")

    if not details:
        raise RuntimeError("Нет данных по заданным критериям")

    # Сохраняем сырые
    df = pd.DataFrame(details)
    df.to_csv(f"{save_prefix}_vacancies.csv", index=False)
    with open(f"{save_prefix}_vacancies.jsonl", "w", encoding="utf-8") as f:
        for row in details:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Агрегация
    aggr = aggregate(df, top_k=30)
    # Сохранение агрегатов
    aggr["skills_counts"].to_csv(f"{save_prefix}_skills_counts.csv", header=["count"])
    pd.DataFrame(aggr["top_requirements_ngrams"], columns=["ngram", "count"]).to_csv(
        f"{save_prefix}_requirements_ngrams.csv", index=False
    )
    pd.DataFrame(aggr["top_responsibilities_ngrams"], columns=["ngram", "count"]).to_csv(
        f"{save_prefix}_responsibilities_ngrams.csv", index=False
    )
    pd.DataFrame(
        [{"skill_a": a, "skill_b": b, "count": c} for (a, b), c in aggr["top_skill_pairs"]]
    ).to_csv(f"{save_prefix}_skill_pairs.csv", index=False)

    # Короткий принт-итог
    print("\nТоп-20 навыков:")
    print(aggr["skills_counts"].head(20))

    print("\nТоп-20 фраз в требованиях:")
    for ng, c in aggr["top_requirements_ngrams"][:20]:
        print(f"{ng}: {c}")

    print("\nТоп-20 фраз в задачах (responsibilities):")
    for ng, c in aggr["top_responsibilities_ngrams"][:20]:
        print(f"{ng}: {c}")

    return {
        "df": df,
        "aggregates": aggr
    }


if __name__ == "__main__":
    # Пример запуска:
    # - должность: "Аналитик данных"
    # - регион: "Москва" (автоматически подберётся id)
    # - период: последние 30 дней
    # - ограничим максимум 1000 вакансий для примера
    result = run_pipeline(
        query_text="Аналитик данных",
        area_query_or_id="Москва",
        professional_role_ids=None,  # можно указать id профессиональных ролей, если знаете
        period_days=30,
        per_page=100,
        max_pages=None,
        max_results=1000,
        save_prefix="hh_analyst_moscow"
    )
