import requests

def run():
    print("Chatbot REST client started. Type '_exit_' to EXIT.\n")

    while True:
        user_input = input("You: ")
        if user_input.strip() == "_exit_":
            print("Goodbye!")
            break

        payload = {"q": user_input}
        try:
            response = requests.post("http://localhost:8080/v1/llm/answer", json=payload)
            response.raise_for_status()
            data = response.json()
            print("AimeAgent:", data.get("ans", ""))
        except requests.exceptions.RequestException as e:
            print(f"HTTP Error: {e}")
            break

if __name__ == '__main__':
    run()
