import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ComicTranslateService, ProcessResponse, TextBlockData, TranslationRequest } from '../../services/comic-translate.service';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
import { ProgressIndicatorComponent, ProgressStep } from '../progress-indicator/progress-indicator.component';
import { TextBlockEditorComponent } from '../text-block-editor/text-block-editor.component';

@Component({
  selector: 'app-translation-result',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './translation-result.component.html',
  styleUrls: ['./translation-result.component.css']
})
export class TranslationResultComponent implements OnInit, OnDestroy {
  @Input() imageId: string = '';
  @Input() sourceLanguage: string = '';
  @Input() targetLanguage: string = '';

  currentStep: string = 'detecting';
  isProcessing: boolean = false;
  processResponse: ProcessResponse | null = null;
  resultImageUrl: SafeUrl | null = null;
  error: string = '';

  steps = [
    { key: 'detecting', label: 'Detecting Text Blocks', icon: '🔍', completed: false },
    { key: 'ocr', label: 'Reading Text', icon: '📖', completed: false },
    { key: 'translating', label: 'Translating', icon: '🌐', completed: false },
    { key: 'inpainting', label: 'Removing Original Text', icon: '🎨', completed: false },
    { key: 'rendering', label: 'Adding Translated Text', icon: '✨', completed: false },
    { key: 'completed', label: 'Completed!', icon: '🎉', completed: false }
  ];

  constructor(
    private comicService: ComicTranslateService,
    private sanitizer: DomSanitizer
  ) { }

  ngOnInit(): void {
    if (this.imageId) {
      this.startTranslationProcess();
    }
  }

  ngOnDestroy(): void {
    if (this.resultImageUrl) {
      URL.revokeObjectURL(this.resultImageUrl as string);
    }
  }

  private async startTranslationProcess(): Promise<void> {
    this.isProcessing = true;
    this.error = '';

    try {
      // Step 1: Detect blocks
      await this.executeStep('detecting', () =>
        this.comicService.detectBlocks(this.imageId)
      );

      // Step 2: OCR
      await this.executeStep('ocr', () =>
        this.comicService.ocrImage(this.imageId)
      );

      // Step 3: Translate
      const translationRequest: TranslationRequest = {
        source_language: this.sourceLanguage,
        target_language: this.targetLanguage,
        extra_context: '',
        use_gpu: true
      };

      await this.executeStep('translating', () =>
        this.comicService.translateImage(this.imageId, translationRequest)
      );

      // Step 4: Inpaint
      await this.executeStep('inpainting', () =>
        this.comicService.inpaintImage(this.imageId)
      );

      // Step 5: Render
      await this.executeStep('rendering', () =>
        this.comicService.renderImage(this.imageId)
      );

      // Step 6: Get result
      await this.loadResultImage();
      this.completeStep('completed');

    } catch (error: any) {
      this.error = error.message || 'An error occurred during translation';
      this.isProcessing = false;
    }
  }

  private async executeStep(stepKey: string, apiCall: () => any): Promise<void> {
    this.currentStep = stepKey;

    try {
      const response = await new Promise<ProcessResponse>((resolve, reject) => {
        apiCall().subscribe({
          next: (res: ProcessResponse) => resolve(res),
          error: reject
        });
      });
      if (response && response.blocks) {
        this.processResponse = response;
      }
      this.completeStep(stepKey);

      // Add delay for better UX
      await this.delay(1000);
    } catch (error) {
      throw error;
    }
  }

  private completeStep(stepKey: string): void {
    const step = this.steps.find(s => s.key === stepKey);
    if (step) {
      step.completed = true;
    }
  }

  private async loadResultImage(): Promise<void> {
    try {
      const blob = await new Promise<Blob>((resolve, reject) => {
        this.comicService.getResultImage(this.imageId).subscribe({
          next: resolve,
          error: reject
        });
      });
      if (blob) {
        const url = URL.createObjectURL(blob);
        this.resultImageUrl = this.sanitizer.bypassSecurityTrustUrl(url);
      }
      this.isProcessing = false;
    } catch (error) {
      throw new Error('Failed to load result image');
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  downloadResult(): void {
    if (this.resultImageUrl) {
      const link = document.createElement('a');
      link.href = this.resultImageUrl as string;
      link.download = `translated_comic_${this.imageId}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }

  restartProcess(): void {
    // Reset all steps
    this.steps.forEach(step => step.completed = false);
    this.currentStep = 'detecting';
    this.isProcessing = false;
    this.error = '';
    this.processResponse = null;

    if (this.resultImageUrl) {
      URL.revokeObjectURL(this.resultImageUrl as string);
      this.resultImageUrl = null;
    }

    // Restart the process
    this.startTranslationProcess();
  }

  getStepClass(step: any): string {
    if (step.completed) return 'step-completed';
    if (step.key === this.currentStep) return 'step-active';
    return 'step-pending';
  }
}
