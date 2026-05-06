from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_ai(ventes, depenses, question):

    prompt = f"""
Tu es un expert en business, comptabilité et stratégie.

Données de l'entreprise:
- Ventes: {ventes}
- Dépenses: {depenses}
- Bénéfice: {ventes - depenses}

Question:
{question}

Réponds de manière professionnelle, claire et stratégique.
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return res.choices[0].message.content

    except Exception as e:
        return f"Erreur IA: {e}"
