from src.graph.workflow import build_graph
from src.category_loader import load_categories

def main():
    print("Starting data collection pipeline...")

    app = build_graph()

    categories = load_categories()
    result = app.invoke({
        "categories": categories,
        "errors": [],

        "enable_raw_qa": False,

        # testing limits
        "articles_per_focus": 2,
        "extra_articles_per_category": 2,
        "max_categories": 1,
        "max_articles": 50,
        "max_chunks_per_article": 100,
        "max_nuggets_per_article": 20,
    })

    print("Topics by category:", result.get("topics_by_category"))
    print("Flat topics:", result.get("topics"))
    print("Errors:", result.get("errors"))
    print("Data collection pipeline finished.")


if __name__ == "__main__":
    main()
