/**
 * SDK Generator Service — generate code snippets for each supported language
 */

export type Language = 'curl' | 'javascript' | 'python' | 'go' | 'ruby';

export interface SnippetOptions {
  language: Language;
  endpoint: string;
  method: string;
  /** Optional API key to embed in the generated snippet */
  apiKey?: string;
}

export interface EndpointInfo {
  method: string;
  path: string;
  description: string;
}

const BASE_URL = 'https://raas-gateway.agencyos-openclaw.workers.dev';

const ENDPOINTS: EndpointInfo[] = [
  { method: 'GET',  path: '/v1/missions',         description: 'List missions for the authenticated tenant' },
  { method: 'POST', path: '/v1/missions',          description: 'Submit a new AI mission (1-5 MCU)' },
  { method: 'GET',  path: '/v1/missions/:id',      description: 'Get mission status and result by ID' },
  { method: 'POST', path: '/v1/missions/batch',    description: 'Batch submit up to 50 missions at once' },
  { method: 'GET',  path: '/v1/credits/balance',   description: 'Get current credit balance' },
  { method: 'GET',  path: '/v1/usage/current',     description: 'Get current daily and monthly usage stats' },
];

export class SdkGeneratorService {
  /** Return all documented endpoints */
  getEndpointList(): EndpointInfo[] {
    return ENDPOINTS;
  }

  /** Generate a single code snippet for the requested language / endpoint */
  generateSnippet(opts: SnippetOptions): string {
    const { language, endpoint, method, apiKey } = opts;
    const url = `${BASE_URL}${endpoint}`;
    const key = apiKey ?? 'YOUR_API_KEY';
    const upperMethod = method.toUpperCase();

    switch (language) {
      case 'curl':
        return this.curl(url, upperMethod, key);
      case 'javascript':
        return this.javascript(url, upperMethod, key);
      case 'python':
        return this.python(url, upperMethod, key);
      case 'go':
        return this.go(url, upperMethod, key);
      case 'ruby':
        return this.ruby(url, upperMethod, key);
      default:
        throw new Error(`Unsupported language: ${language}`);
    }
  }

  /** Generate a full SDK client class (javascript or python only) */
  generateFullSDK(language: 'javascript' | 'python'): string {
    return language === 'javascript'
      ? this.javascriptFullSdk()
      : this.pythonFullSdk();
  }

  // --- private snippet builders ---

  private curl(url: string, method: string, key: string): string {
    const hasBody = ['POST', 'PUT', 'PATCH'].includes(method);
    const bodyFlag = hasBody
      ? `\\\n  -H 'Content-Type: application/json' \\\n  -d '{"goal":"your goal here","complexity":"standard"}'`
      : '';
    return `curl -X ${method} '${url}' \\\n  -H 'X-API-Key: ${key}'${bodyFlag}`;
  }

  private javascript(url: string, method: string, key: string): string {
    const hasBody = ['POST', 'PUT', 'PATCH'].includes(method);
    const bodyLines = hasBody
      ? `\n  body: JSON.stringify({ goal: 'your goal here', complexity: 'standard' }),`
      : '';
    return `const response = await fetch('${url}', {
  method: '${method}',
  headers: {
    'X-API-Key': '${key}',
    'Content-Type': 'application/json',
  },${bodyLines}
});
const data = await response.json();
console.log(data);`;
  }

  private python(url: string, method: string, key: string): string {
    const hasBody = ['POST', 'PUT', 'PATCH'].includes(method);
    const bodyLines = hasBody
      ? `\npayload = {"goal": "your goal here", "complexity": "standard"}\nresponse = requests.${method.toLowerCase()}(url, headers=headers, json=payload)`
      : `\nresponse = requests.${method.toLowerCase()}(url, headers=headers)`;
    return `import requests

url = '${url}'
headers = {'X-API-Key': '${key}', 'Content-Type': 'application/json'}
${bodyLines}
print(response.json())`;
  }

  private go(url: string, method: string, key: string): string {
    const hasBody = ['POST', 'PUT', 'PATCH'].includes(method);
    const bodySection = hasBody
      ? `\n\tbody := strings.NewReader(\`{"goal":"your goal here","complexity":"standard"}\`)\n\treq, _ := http.NewRequest("${method}", "${url}", body)\n\treq.Header.Set("Content-Type", "application/json")`
      : `\n\treq, _ := http.NewRequest("${method}", "${url}", nil)`;
    return `package main

import (
\t"fmt"
\t"io"
\t"net/http"${hasBody ? '\n\t"strings"' : ''}
)

func main() {${bodySection}
\treq.Header.Set("X-API-Key", "${key}")
\tclient := &http.Client{}
\tresp, _ := client.Do(req)
\tdefer resp.Body.Close()
\tbody, _ := io.ReadAll(resp.Body)
\tfmt.Println(string(body))
}`;
  }

  private ruby(url: string, method: string, key: string): string {
    const hasBody = ['POST', 'PUT', 'PATCH'].includes(method);
    const rubyMethod = method.toLowerCase();
    const bodySection = hasBody
      ? `\nrequest.body = '{"goal":"your goal here","complexity":"standard"}'`
      : '';
    // Ruby Net::HTTP class names: Get, Post, Put, Delete, Patch, Head
    const rubyClass = rubyMethod.charAt(0).toUpperCase() + rubyMethod.slice(1);
    return `require 'net/http'
require 'json'

uri = URI('${url}')
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true

request = Net::HTTP::${rubyClass}.new(uri)
request['X-API-Key'] = '${key}'
request['Content-Type'] = 'application/json'${bodySection}

response = http.request(request)
puts JSON.parse(response.body)`;
  }

  // --- full SDK templates ---

  private javascriptFullSdk(): string {
    return `/**
 * Mekong RaaS Gateway SDK — JavaScript / TypeScript
 */
class MekongClient {
  constructor(apiKey, baseUrl = '${BASE_URL}') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async #request(method, path, body) {
    const res = await fetch(\`\${this.baseUrl}\${path}\`, {
      method,
      headers: { 'X-API-Key': this.apiKey, 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw new Error(\`API error \${res.status}: \${await res.text()}\`);
    return res.json();
  }

  listMissions(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.#request('GET', \`/v1/missions\${qs ? '?' + qs : ''}\`);
  }

  submitMission(goal, options = {}) {
    return this.#request('POST', '/v1/missions', { goal, ...options });
  }

  getMission(id) { return this.#request('GET', \`/v1/missions/\${id}\`); }

  batchMissions(goals) {
    return this.#request('POST', '/v1/missions/batch', { missions: goals });
  }

  getBalance() { return this.#request('GET', '/v1/credits/balance'); }

  getCurrentUsage() { return this.#request('GET', '/v1/usage/current'); }
}

module.exports = { MekongClient };`;
  }

  private pythonFullSdk(): string {
    return `"""
Mekong RaaS Gateway SDK — Python
"""
import requests

class MekongClient:
    def __init__(self, api_key: str, base_url: str = "${BASE_URL}"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        })

    def _request(self, method: str, path: str, **kwargs):
        resp = self.session.request(method, f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def list_missions(self, **params):
        return self._request("GET", "/v1/missions", params=params)

    def submit_mission(self, goal: str, **options):
        return self._request("POST", "/v1/missions", json={"goal": goal, **options})

    def get_mission(self, mission_id: str):
        return self._request("GET", f"/v1/missions/{mission_id}")

    def batch_missions(self, goals: list):
        return self._request("POST", "/v1/missions/batch", json={"missions": goals})

    def get_balance(self):
        return self._request("GET", "/v1/credits/balance")

    def get_current_usage(self):
        return self._request("GET", "/v1/usage/current")`;
  }
}
