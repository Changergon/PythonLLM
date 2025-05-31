import matplotlib.pyplot as plt

def plot_ratings(ratings):
    plt.figure(figsize=(10, 5))
    plt.bar(["GigaChat", "Local LLM"],
            [sum(ratings["gigachat"])/len(ratings["gigachat"]),
             sum(ratings["local_llm"])/len(ratings["local_llm"])])
    plt.title("Average Ratings")
    plt.ylabel("Score")
    plt.show()