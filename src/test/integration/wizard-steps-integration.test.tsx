import { describe, test, expect } from 'vitest';
import { render } from '@testing-library/react';
import ModelSelectionStep from '../../components/wizard/ModelSelectionStep';
import SmartConfigurationStep from '../../components/wizard/SmartConfigurationStep';
import { WizardState } from '../../types/wizard';

describe('Wizard Steps Integration', () => {
  const mockWizardState: WizardState = {
    currentStep: 3,
    profile: {
      id: 'chatbot',
      name: 'Chatbot Assistant',
      description: 'Test profile',
      use_case: 'chatbot',
      icon: '💬',
      example_use_cases: ['Chat'],
      config: {
        lora_r: 16,
        lora_alpha: 32,
        lora_dropout: 0.05,
        target_modules: ['q_proj', 'v_proj'],
        learning_rate: 2e-4,
        num_epochs: 3,
        warmup_ratio: 0.1,
        max_seq_length: 2048,
        weight_decay: 0.01,
        max_grad_norm: 1.0,
        scheduler: 'cosine',
      },
      requirements: {
        min_gpu_memory_gb: 8,
        recommended_gpu_memory_gb: 16,
        min_dataset_size: 100,
        recommended_dataset_size: 1000,
        estimated_time_per_epoch_minutes: 30,
      },
      tags: ['chat', 'conversation'],
    },
    dataset: {
      id: 'test-dataset',
      name: 'test.json',
      path: '/path/to/test.json',
      format: 'json',
      size: 1024000,
      num_samples: 500,
    },
    model: null,
    config: {},
    estimates: null,
    validation: [],
  };

  test('ModelSelectionStep renders without crashing', () => {
    const { container } = render(
      <ModelSelectionStep
        wizardState={mockWizardState}
        onModelSelect={() => {}}
      />
    );
    expect(container).toBeTruthy();
  });

  test('SmartConfigurationStep renders without crashing', () => {
    const wizardStateWithModel: WizardState = {
      ...mockWizardState,
      model: {
        model_id: 'meta-llama/Llama-2-7b-hf',
        author: 'meta-llama',
        model_name: 'Llama-2-7b-hf',
        downloads: 1000000,
        likes: 5000,
        tags: ['llama', 'text-generation'],
        pipeline_tag: 'text-generation',
        library_name: 'transformers',
        size_mb: 13000,
        parameters: 7000,
        architecture: 'LlamaForCausalLM',
        license: 'llama2',
      },
    };

    const { container } = render(
      <SmartConfigurationStep
        wizardState={wizardStateWithModel}
        onConfigUpdate={() => {}}
      />
    );
    expect(container).toBeTruthy();
  });
});
