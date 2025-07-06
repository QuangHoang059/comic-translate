import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface ProgressStep {
  key: string;
  label: string;
  icon: string;
  completed: boolean;
  error?: boolean;
}

@Component({
  selector: 'app-progress-indicator',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './progress-indicator.component.html',
  styleUrls: ['./progress-indicator.component.css']
})
export class ProgressIndicatorComponent {
  @Input() steps: ProgressStep[] = [];
  @Input() currentStep: string = '';
  @Input() isProcessing: boolean = false;
  @Input() error: string = '';

  getStepClass(step: ProgressStep): string {
    const classes = ['progress-step'];

    if (step.completed) {
      classes.push('completed');
    } else if (step.error) {
      classes.push('error');
    } else if (step.key === this.currentStep && this.isProcessing) {
      classes.push('active');
    } else {
      classes.push('pending');
    }

    return classes.join(' ');
  }

  getStepStatus(step: ProgressStep): string {
    if (step.error) {
      return 'error';
    } else if (step.completed) {
      return 'completed';
    } else if (step.key === this.currentStep && this.isProcessing) {
      return 'processing';
    } else {
      return 'pending';
    }
  }

  getProgressPercentage(): number {
    if (this.steps.length === 0) return 0;

    const completedSteps = this.steps.filter(step => step.completed).length;
    const currentStepIndex = this.steps.findIndex(step => step.key === this.currentStep);

    let progress = (completedSteps / this.steps.length) * 100;

    // Add partial progress for current step
    if (currentStepIndex >= 0 && this.isProcessing) {
      progress += (1 / this.steps.length) * 50; // 50% of current step
    }

    return Math.min(progress, 100);
  }

  getEstimatedTimeRemaining(): string {
    const completedSteps = this.steps.filter(step => step.completed).length;
    const totalSteps = this.steps.length;
    const remainingSteps = totalSteps - completedSteps;

    if (remainingSteps <= 0) return '0 minutes';

    // Rough estimation: 30 seconds per step
    const estimatedMinutes = Math.ceil((remainingSteps * 30) / 60);

    if (estimatedMinutes < 1) return 'Less than 1 minute';
    if (estimatedMinutes === 1) return '1 minute';
    return `${estimatedMinutes} minutes`;
  }

  getRandomFunFact(): string {
    const funFacts = [
      'Our AI analyzes each text bubble to understand context and provide natural translations!',
      'The text detection algorithm can identify text at various angles and sizes.',
      'Machine translation has improved dramatically with neural networks and deep learning.',
      'Comics are translated into over 40 languages worldwide!',
      'The first comic strip was published in 1895 in the New York World.',
      'Manga accounts for about 40% of all books and magazines sold in Japan.',
      'The word "comic" comes from the Greek word "komikos" meaning "of or relating to comedy".',
      'Our inpainting technology can seamlessly remove text while preserving the artwork.',
      'AI translation considers cultural context, not just literal word meanings.',
      'The average comic page contains 3-7 speech bubbles or text blocks.'
    ];

    return funFacts[Math.floor(Math.random() * funFacts.length)];
  }
}
