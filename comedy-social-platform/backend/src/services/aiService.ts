import { HumorStyle } from '../types';

// Mock AI service - in production, you would integrate with OpenAI or similar
class AIService {
  private mockJokes: Record<HumorStyle, string[]> = {
    [HumorStyle.DARK]: [
      "I told my wife she was drawing her eyebrows too high. She looked surprised.",
      "My therapist says I have a preoccupation with vengeance. We'll see about that.",
      "I bought the world's worst thesaurus yesterday. Not only is it terrible, it's terrible."
    ],
    [HumorStyle.WHOLESOME]: [
      "Why don't scientists trust atoms? Because they make up everything!",
      "What do you call a bear with no teeth? A gummy bear!",
      "Why did the scarecrow win an award? He was outstanding in his field!"
    ],
    [HumorStyle.SATIRICAL]: [
      "I love how we cook bacon and bake cookies. English is weird.",
      "The early bird might get the worm, but the second mouse gets the cheese.",
      "I used to hate facial hair, but then it grew on me."
    ],
    [HumorStyle.OBSERVATIONAL]: [
      "Ever notice how 'abbreviated' is such a long word?",
      "Why do we park in driveways and drive on parkways?",
      "If 7-Eleven is open 24 hours, why do they have locks on the doors?"
    ],
    [HumorStyle.SURREAL]: [
      "Yesterday I accidentally swallowed some food coloring. The doctor says I'm OK, but I feel like I've dyed a little inside.",
      "I invented a new word: Plagiarism!",
      "Time flies like an arrow. Fruit flies like a banana."
    ],
    [HumorStyle.WORDPLAY]: [
      "I wondered why the baseball kept getting bigger. Then it hit me.",
      "A bicycle can't stand on its own because it's two-tired.",
      "The math teacher called in sick with algebra."
    ],
    [HumorStyle.PHYSICAL]: [
      "I tried to catch some fog earlier. I mist.",
      "When life gives you melons, you might be dyslexic.",
      "I used to be a banker, but I lost interest."
    ],
    [HumorStyle.SELF_DEPRECATING]: [
      "I'm reading a book about anti-gravity. It's impossible to put down!",
      "I'm on a seafood diet. I see food and I eat it.",
      "I told my cat a joke about dogs. He didn't find it a-mew-sing."
    ]
  };

  async generateJoke(humorStyle: HumorStyle, topic?: string): Promise<string> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    const jokes = this.mockJokes[humorStyle] || this.mockJokes[HumorStyle.WHOLESOME];
    const randomJoke = jokes[Math.floor(Math.random() * jokes.length)];

    // In a real implementation, you would call OpenAI API here
    // const response = await openai.createCompletion({
    //   model: "text-davinci-003",
    //   prompt: `Generate a ${humorStyle} joke about ${topic || 'general topics'}`,
    //   max_tokens: 100,
    //   temperature: 0.9,
    // });

    return randomJoke;
  }

  async analyzeHumor(content: string): Promise<{
    humorStyles: HumorStyle[];
    confidence: number;
  }> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    // Mock analysis - in production, use ML model
    const words = content.toLowerCase().split(' ');
    const detectedStyles: HumorStyle[] = [];

    // Simple keyword-based detection
    if (words.some(word => ['dark', 'death', 'murder', 'pain'].includes(word))) {
      detectedStyles.push(HumorStyle.DARK);
    }
    if (words.some(word => ['cute', 'sweet', 'wholesome', 'nice'].includes(word))) {
      detectedStyles.push(HumorStyle.WHOLESOME);
    }
    if (words.some(word => ['pun', 'play', 'word'].includes(word))) {
      detectedStyles.push(HumorStyle.WORDPLAY);
    }
    if (words.some(word => ['observe', 'notice', 'why', 'how'].includes(word))) {
      detectedStyles.push(HumorStyle.OBSERVATIONAL);
    }

    // Default to wholesome if no style detected
    if (detectedStyles.length === 0) {
      detectedStyles.push(HumorStyle.WHOLESOME);
    }

    return {
      humorStyles: detectedStyles,
      confidence: Math.random() * 0.4 + 0.6 // 60-100% confidence
    };
  }

  async generatePersonalizedContent(userPreferences: {
    humorStyles: HumorStyle[];
    topics: string[];
  }): Promise<string> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500));

    const preferredStyle = userPreferences.humorStyles[0] || HumorStyle.WHOLESOME;
    const topic = userPreferences.topics[0] || 'general';

    return this.generateJoke(preferredStyle, topic);
  }

  async moderateContent(content: string): Promise<{
    isAppropriate: boolean;
    reason?: string;
    confidence: number;
  }> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));

    const inappropriateWords = ['spam', 'hate', 'violence', 'explicit'];
    const hasInappropriateContent = inappropriateWords.some(word =>
      content.toLowerCase().includes(word)
    );

    return {
      isAppropriate: !hasInappropriateContent,
      reason: hasInappropriateContent ? 'Contains inappropriate content' : undefined,
      confidence: 0.85
    };
  }
}

export const aiService = new AIService();