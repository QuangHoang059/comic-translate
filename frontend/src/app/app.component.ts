import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ImageUploadComponent } from './components/image-upload/image-upload.component';
import { TranslationResultComponent } from './components/translation-result/translation-result.component';
import { ProcessResponse } from './services/comic-translate.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule, ImageUploadComponent, TranslationResultComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'Comic Translate';
  currentView: 'upload' | 'processing' = 'upload';
  uploadResponse: ProcessResponse | null = null;
  sourceLanguage: string = '';
  targetLanguage: string = '';
  errorMessage: string = '';

  onImageUploaded(response: ProcessResponse): void {
    this.uploadResponse = response;
    this.currentView = 'processing';
    this.errorMessage = '';
  }

  onUploadError(error: string): void {
    this.errorMessage = error;
    this.uploadResponse = null;
  }

  onLanguagesSelected(source: string, target: string): void {
    this.sourceLanguage = source;
    this.targetLanguage = target;
  }

  resetToUpload(): void {
    this.currentView = 'upload';
    this.uploadResponse = null;
    this.errorMessage = '';
  }
}
