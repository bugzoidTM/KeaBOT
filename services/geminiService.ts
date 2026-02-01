import { GoogleGenAI, Chat, GenerateContentResponse } from "@google/genai";

const apiKey = process.env.API_KEY || '';

// Singleton instance management
let ai: GoogleGenAI | null = null;

const getAIClient = (): GoogleGenAI => {
  if (!ai) {
    ai = new GoogleGenAI({ apiKey });
  }
  return ai;
};

export const createChatSession = (systemInstruction?: string): Chat => {
  const client = getAIClient();
  return client.chats.create({
    model: 'gemini-2.5-flash-latest', // Using a fast, conversational model
    config: {
      systemInstruction: systemInstruction || "You are KeaBOT, a helpful, professional, and intelligent AI assistant.",
    },
  });
};

export const sendMessageStream = async (
  chat: Chat, 
  message: string, 
  onChunk: (text: string) => void
): Promise<string> => {
  let fullResponse = "";
  try {
    const resultStream = await chat.sendMessageStream({ message });
    
    for await (const chunk of resultStream) {
      const c = chunk as GenerateContentResponse;
      if (c.text) {
        fullResponse += c.text;
        onChunk(fullResponse);
      }
    }
  } catch (error) {
    console.error("Gemini API Error:", error);
    throw error;
  }
  return fullResponse;
};