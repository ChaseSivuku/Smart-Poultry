// Mock data service for Vercel deployment
export class MockDataService {
  private static instance: MockDataService;
  private data = {
    temperature: 25.5,
    humidity: 65.0,
    tankLevel: 75,
    feed: 45,
    light: 350
  };

  private constructor() {
    // Simulate data changes
    setInterval(() => {
      this.data.temperature += (Math.random() - 0.5) * 2;
      this.data.humidity += (Math.random() - 0.5) * 5;
      this.data.tankLevel += (Math.random() - 0.5) * 3;
      this.data.feed += (Math.random() - 0.5) * 2;
      this.data.light += (Math.random() - 0.5) * 20;
      
      // Keep values in reasonable ranges
      this.data.temperature = Math.max(15, Math.min(35, this.data.temperature));
      this.data.humidity = Math.max(30, Math.min(90, this.data.humidity));
      this.data.tankLevel = Math.max(10, Math.min(100, this.data.tankLevel));
      this.data.feed = Math.max(5, Math.min(80, this.data.feed));
      this.data.light = Math.max(100, Math.min(500, this.data.light));
    }, 2000);
  }

  public static getInstance(): MockDataService {
    if (!MockDataService.instance) {
      MockDataService.instance = new MockDataService();
    }
    return MockDataService.instance;
  }

  public getSensorData() {
    return Promise.resolve(this.data);
  }

  public async sendToAssistant(question: string) {
    // Mock Gemini response
    const responses = [
      `Based on the current data: Temperature is ${this.data.temperature.toFixed(1)}°C, which is within normal range.`,
      `Your water tank is at ${this.data.tankLevel.toFixed(1)}% capacity. Consider refilling if it drops below 20%.`,
      `The current humidity level of ${this.data.humidity.toFixed(1)}% is optimal for poultry health.`,
      `Light intensity is ${this.data.light.toFixed(0)} lux. This provides adequate lighting for your chickens.`,
      `Feed levels are at ${this.data.feed.toFixed(1)}kg. Monitor consumption patterns for optimal feeding.`
    ];
    
    return {
      answer: responses[Math.floor(Math.random() * responses.length)],
      timestamp: new Date().toISOString()
    };
  }
}
