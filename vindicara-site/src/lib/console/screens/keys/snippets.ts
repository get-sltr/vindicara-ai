// The setup snippets the Keys screen and /get-started render. One source, so
// the two surfaces cannot drift, and so every snippet matches the real SDK
// signatures (AIRRecorder(user_intent=...), instrument_*(client, recorder),
// AIRCallbackHandler(recorder=recorder)).
export const DEFAULT_CLOUD_URL = 'https://cloud.vindicara.io';
export const KEY_PLACEHOLDER = 'air_<your key>';

export interface Snippet {
  id: string;
  name: string;
  code: string;
}

const INTENT = 'Summarize the quarterly report';

export const SNIPPETS: Snippet[] = [
  {
    id: 'openai',
    name: 'OpenAI (and any compatible API)',
    code: `from openai import OpenAI
from airsdk import AIRRecorder
from airsdk.integrations.openai import instrument_openai

recorder = AIRRecorder(user_intent="${INTENT}")
client = instrument_openai(OpenAI(), recorder)
# use client exactly as before; every call is signed locally and mirrored to AIR Cloud`
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    code: `from anthropic import Anthropic
from airsdk import AIRRecorder
from airsdk.integrations.anthropic import instrument_anthropic

recorder = AIRRecorder(user_intent="${INTENT}")
client = instrument_anthropic(Anthropic(), recorder)
# use client exactly as before`
  },
  {
    id: 'langchain',
    name: 'LangChain',
    code: `from airsdk import AIRRecorder, AIRCallbackHandler

recorder = AIRRecorder(user_intent="${INTENT}")
handler = AIRCallbackHandler(recorder=recorder)
agent.invoke({"input": "${INTENT}"}, config={"callbacks": [handler]})`
  },
  {
    id: 'gemini',
    name: 'Google Gemini',
    code: `from google import genai
from airsdk import AIRRecorder, instrument_gemini

recorder = AIRRecorder(user_intent="${INTENT}")
client = instrument_gemini(genai.Client(), recorder)
# use client exactly as before`
  },
  {
    id: 'llamaindex',
    name: 'LlamaIndex',
    code: `from llama_index.llms.openai import OpenAI as LlamaOpenAI
from airsdk import AIRRecorder
from airsdk.integrations.llamaindex import instrument_llamaindex

recorder = AIRRecorder(user_intent="${INTENT}")
llm = instrument_llamaindex(LlamaOpenAI(model="gpt-4o-mini"), recorder)`
  },
  {
    id: 'plain',
    name: 'Any framework (plain recorder)',
    code: `from airsdk import AIRRecorder

recorder = AIRRecorder(user_intent="${INTENT}")
recorder.llm_start(prompt="${INTENT}")
recorder.tool_start(tool_name="search", tool_args={"q": "Q3 revenue"})
recorder.tool_end(tool_output="Revenue up 12% QoQ")
recorder.agent_finish(final_output="Q3 revenue rose 12% quarter over quarter.")`
  }
];

// The shell block every tab starts with. The URL line appears only when the
// console is not talking to the default hosted service (self-hosted, local dev).
export function shellHeader(apiKey: string | null, cloudUrl: string): string {
  const lines = ['pip install "projectair>=1.4"', `export AIRSDK_CLOUD_API_KEY=${apiKey ?? KEY_PLACEHOLDER}`];
  const url = cloudUrl.replace(/\/$/, '');
  if (url && url !== DEFAULT_CLOUD_URL) lines.push(`export AIRSDK_CLOUD_URL=${url}`);
  return lines.join('\n');
}

export function runLinkHint(consoleUrl: string): string {
  return `Run it. The terminal prints your run link: ${consoleUrl.replace(/\/$/, '')}/runs/<run_id>`;
}
