import { Brain, Zap, Shield, Sparkles, ArrowRight } from "lucide-react";
import React from "react";

interface WelcomeScreenProps {
  onGetStarted: () => void;
  onSkip: () => void;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  onGetStarted,
  onSkip,
}) => {
  const features = [
    {
      icon: Brain,
      title: "Smart Configuration",
      description:
        "Automatically optimizes settings based on your hardware and dataset",
      color: "text-accent-primary",
    },
    {
      icon: Zap,
      title: "Real-Time Monitoring",
      description:
        "Watch your model train with live metrics and visual feedback",
      color: "text-accent-success",
    },
    {
      icon: Shield,
      title: "Auto-Recovery",
      description: "Detects and fixes training issues automatically",
      color: "text-accent-warning",
    },
    {
      icon: Sparkles,
      title: "One-Click Export",
      description:
        "Deploy to HuggingFace, Ollama, and more with a single click",
      color: "text-accent-info",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-bg-primary via-dark-bg-secondary to-dark-bg-primary flex items-center justify-center p-24">
      <div className="max-w-4xl w-full">
        {/* Header */}
        <div className="text-center mb-48 animate-fade-in">
          <div className="inline-flex items-center justify-center w-80 h-80 bg-gradient-to-br from-accent-primary to-accent-info rounded-full mb-24">
            <Brain size={40} className="text-white" />
          </div>
          <h1 className="text-display mb-16">Welcome to PEFT Studio</h1>
          <p className="text-h3 text-dark-text-secondary max-w-2xl mx-auto">
            Fine-tune Large Language Models with ease. No PhD required.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-24 mb-48">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="card card-hover animate-fade-in"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="flex items-start gap-16">
                  <div
                    className={`w-48 h-48 rounded-lg bg-dark-bg-tertiary flex items-center justify-center flex-shrink-0`}
                  >
                    <Icon size={24} className={feature.color} />
                  </div>
                  <div>
                    <h3 className="text-h3 mb-8">{feature.title}</h3>
                    <p className="text-body text-dark-text-secondary">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* CTA Buttons */}
        <div
          className="flex items-center justify-center gap-16 animate-fade-in"
          style={{ animationDelay: "400ms" }}
        >
          <button
            onClick={onGetStarted}
            className="btn btn-primary btn-lg group"
          >
            Get Started
            <ArrowRight
              size={20}
              className="ml-8 group-hover:translate-x-4 transition-transform"
            />
          </button>
          <button onClick={onSkip} className="btn btn-secondary btn-lg">
            Skip Tour
          </button>
        </div>

        {/* Footer Note */}
        <p
          className="text-center text-small text-dark-text-tertiary mt-24 animate-fade-in"
          style={{ animationDelay: "500ms" }}
        >
          This tour will take about 2 minutes and show you the key features
        </p>
      </div>
    </div>
  );
};

export default WelcomeScreen;
