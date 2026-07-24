/** Mekong auth port definitions for /login. */
export type AuthPort = {
  key: string;
  title: string;
  description: string;
  kind: "remote_api" | "custom_jwt" | "local_model";
  suggestedModel?: string;
};

export const AUTH_PORTS: AuthPort[] = [
  {
    key: "claudeai",
    title: "Claude account with subscription",
    description: "Pro, Max, Team, or Enterprise",
    kind: "remote_api"
  },
  {
    key: "console",
    title: "Anthropic Console account",
    description: "API usage billing",
    kind: "remote_api"
  },
  {
    key: "bedrock_vertex_foundry",
    title: "3rd-party platform",
    description: "Amazon Bedrock, Microsoft Foundry, or Vertex AI",
    kind: "remote_api"
  },
  {
    key: "zunef",
    title: "ZuneF gateway",
    description: "Anthropic-compatible API through ZuneF",
    kind: "custom_jwt",
    suggestedModel: "mekong-fable-5"
  },
  {
    key: "local_m1_max",
    title: "Local LLM on MacBook M1 Max",
    description: "Local runtime without remote API",
    kind: "local_model",
    suggestedModel: "local-llm"
  }
];

export function resolvePort(key: string): AuthPort {
  const port = AUTH_PORTS.find((item) => item.key === key);
  if (!port) throw new Error(`Unknown port: ${key}`);
  return port;
}
