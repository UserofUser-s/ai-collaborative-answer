#!/usr/bin/env python3
"""
Collaborative AI System
Multiple local Ollama models debate using Wikipedia API for facts,
interactive role assignment, concise summarization,
and strict system instructions requiring specific answers.
"""

import sys
import time
import threading
from itertools import cycle
from typing import List, Dict, Any
import json
import requests
import ollama

class WikiSearcher:
    """Simple factual lookup using Wikipedia API"""
    def search(self, query: str, sentences: int = 2) -> List[Dict[str, str]]:
        """
        Perform a Wikipedia search: fetch the page extract for the best match.
        Returns a list with one dict containing 'title', 'snippet', and 'url'.
        """
        endpoint = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'format': 'json',
            'prop': 'extracts',
            'exintro': True,
            'explaintext': True,
            'titles': query,
            'redirects': True
        }
        try:
            resp = requests.get(endpoint, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"Wiki search error: HTTP request failed: {e}")
            return [{'title': 'Search Error', 'snippet': f'Request failed: {e}', 'url': ''}]
        except ValueError:
            print("Wiki search error: invalid JSON response")
            return [{'title': 'Search Error', 'snippet': 'Invalid JSON from Wikipedia API', 'url': ''}]

        pages = data.get('query', {}).get('pages', {})
        results = []
        for pid, page in pages.items():
            if 'extract' in page and page['extract']:
                title = page.get('title', '')
                words = page['extract'].split()
                snippet = ' '.join(words[:sentences * 20])
                url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                results.append({'title': title, 'snippet': snippet, 'url': url})
                break

        if not results:
            results.append({'title': 'No Results Found', 'snippet': '', 'url': ''})
        return results

class CollaborativeAI:
    def __init__(self, models: List[str], advocate: str, critic: str,
                 summarizer: str, verbose: bool = False):
        self.models = models
        self.advocate = advocate
        self.critic = critic
        self.summarizer = summarizer
        self.verbose = verbose
        self.searcher = WikiSearcher()

    def wiki_tool(self, query: str) -> str:
        results = self.searcher.search(query)
        out = "Wikipedia facts:\n"
        for i, r in enumerate(results, 1):
            out += f"{i}. {r['title']}\n   {r['snippet']}\n   URL: {r['url']}\n\n"
        return out

    def call_model(self, model_name: str, prompt: str,
                   use_tools: bool = True) -> str:
        tools = []
        if use_tools:
            tools = [{
                'type': 'function',
                'function': {
                    'name': 'wiki_search',
                    'description': 'Lookup facts on Wikipedia',
                    'parameters': {
                        'type': 'object',
                        'properties': {'query': {'type': 'string'}},
                        'required': ['query']
                    }
                }
            }]

        sys_prompt = (
            f"You are {model_name}. You must provide a specific, concrete answer "
            f"to the user’s prompt. Respond according to your assigned role "
            f"(Advocate, Critic, or Summarizer)."
        )
        messages = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': prompt}
        ]
        try:
            if use_tools:
                resp = ollama.chat(model=model_name, messages=messages, tools=tools)
            else:
                resp = ollama.chat(model=model_name, messages=messages)
        except Exception as e:
            return f"Error calling {model_name}: {e}"

        content = resp['message'].get('content', '').strip()

        if use_tools and resp['message'].get('tool_calls'):
            for tc in resp['message']['tool_calls']:
                if tc['function']['name'] == 'wiki_search':
                    q = tc['function']['arguments'].get('query', '')
                    tool_res = self.wiki_tool(q)
                    messages.append(resp['message'])
                    messages.append({'role': 'tool', 'content': tool_res, 'tool_call_id': tc.get('id')})
                    try:
                        resp2 = ollama.chat(model=model_name, messages=messages)
                        content = resp2['message'].get('content', '').strip()
                    except Exception:
                        pass

        return content

    def debate(self, topic: str, rounds: int = 3) -> Dict[str, Any]:
        if self.verbose:
            print(f"🤖 Starting debate on: {topic}\n{'='*60}")
        log = []
        last_stmt = f"Present your opening position on: {topic}"
        for r in range(1, rounds + 1):
            # Advocate
            if self.verbose:
                print(f"\n--- Round {r} | Advocate ({self.advocate}) ---")
            adv = self.call_model(self.advocate, last_stmt, use_tools=True)
            if self.verbose:
                print(f"{self.advocate}: {adv}")
            log.append({'round': r, 'role': 'Advocate', 'model': self.advocate, 'content': adv})

            # Critic
            if self.verbose:
                print(f"--- Round {r} | Critic ({self.critic}) ---")
            crit = self.call_model(self.critic, f"Critically analyze: {adv}", use_tools=True)
            if self.verbose:
                print(f"{self.critic}: {crit}")
            log.append({'round': r, 'role': 'Critic', 'model': self.critic, 'content': crit})

            last_stmt = crit
            time.sleep(1)

        # Summarizer without tools
        summary = self.call_model(self.summarizer,
                                  f"Provide a concise final decision on: {topic}",
                                  use_tools=False)
        if self.verbose:
            print(f"\n{'='*60}\n🏁 Debate concluded!\nFinal decision by {self.summarizer}: {summary}\n")
        return {'log': log, 'final': summary}

    def save_debate(self, result: Dict[str, Any], filename: str = None):
        if not filename:
            filename = f"debate_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 Debate saved to {filename}")

if __name__ == '__main__':
    verbose = any(a in ('-v', '-verbose', '--verbose') for a in sys.argv[1:])
    ml = ollama.list()
    entries = getattr(ml, 'models', ml if isinstance(ml, list) else [])
    available = [getattr(m, 'model', m.get('model', m.get('name'))) for m in entries]

    print("🚀 Collaborative AI System Starting...")
    if not available:
        print("❌ No models installed. Please install Ollama models or specify via --models.")
        sys.exit(1)

    print("Available models:")
    for idx, name in enumerate(available, 1):
        print(f"{idx}. {name}")

    def choose(role: str) -> str:
        while True:
            sel = input(f"Choose {role} model number: ")
            if sel.isdigit() and 1 <= int(sel) <= len(available):
                return available[int(sel) - 1]
            print("Invalid selection. Try again.")

    advocate = choose('Advocate')
    critic = choose('Critic')
    summarizer = choose('Summarizer')

    ai = CollaborativeAI(available, advocate, critic, summarizer, verbose)
    while True:
        topic = input("\n💭 Enter debate topic (or 'quit'): ").strip()
        if topic.lower() in ('quit', 'exit', 'q'):
            print("👋 Goodbye!")
            break
        try:
            rnds = int(input("🔄 Rounds (default 3): ") or "3")
        except ValueError:
            rnds = 3

        if verbose:
            res = ai.debate(topic, rounds=rnds)
            print(f"🔔 Final decision: {res['final']}")
        else:
            container: Dict[str, Any] = {}
            t = threading.Thread(target=lambda: container.update({'res': ai.debate(topic, rounds=rnds)}), daemon=True)
            t.start()
            spin = cycle(['|', '/', '-', '\\'])
            while t.is_alive():
                sys.stdout.write(next(spin))
                sys.stdout.flush()
                time.sleep(0.1)
                sys.stdout.write('\b')
            print(f"\n🏁 Final decision: {container['res']['final']}")
            res = container['res']

        if input("\n💾 Save debate? (y/n): ").lower().startswith('y'):
            ai.save_debate(res)
