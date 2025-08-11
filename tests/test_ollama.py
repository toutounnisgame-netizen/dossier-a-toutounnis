import ollama

# Test direct
try:
    client = ollama.Client(host='http://localhost:11434')
    response = client.generate(
        model='llama3.2',
        prompt='Dis juste "Bonjour"'
    )
    print("✅ Connexion OK !")
    print(f"Réponse : {response['response']}")
except Exception as e:
    print(f"❌ Erreur : {e}")