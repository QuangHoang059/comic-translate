import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ComicTranslateService, ProcessResponse } from '../../services/comic-translate.service';
import { LanguageSelectorComponent } from '../language-selector/language-selector.component';
import { FilePreviewComponent } from '../file-preview/file-preview.component';
import { SettingsComponent, TranslationSettings } from '../settings/settings.component';

@Component({
  selector: 'app-image-upload',
  standalone: true,
  imports: [CommonModule, FormsModule, LanguageSelectorComponent, FilePreviewComponent, SettingsComponent],
  templateUrl: './image-upload.component.html',
  styleUrls: ['./image-upload.component.css']
})
export class ImageUploadComponent {
  @Output() imageUploaded = new EventEmitter<ProcessResponse>();
  @Output() uploadError = new EventEmitter<string>();

  selectedFile: File | null = null;
  sourceLanguage: string = 'Japanese';
  targetLanguage: string = 'Vietnamese';
  isUploading: boolean = false;
  dragOver: boolean = false;
  supportedLanguages: string[] = [];

  settings: TranslationSettings = {
    useGpu: true,
    extraContext: '',
    preserveFormatting: true,
    detectVerticalText: true,
    confidenceThreshold: 0.7
  };

  constructor(private comicService: ComicTranslateService) {
    this.supportedLanguages = this.comicService.getSupportedLanguages();
  }

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.validateAndSetFile(file);
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.dragOver = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragOver = false;

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.validateAndSetFile(files[0]);
    }
  }

  private validateAndSetFile(file: File): void {
    // Check file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      this.uploadError.emit('Please select a valid image file (JPEG, PNG, WebP)');
      return;
    }

    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      this.uploadError.emit('File size must be less than 10MB');
      return;
    }

    this.selectedFile = file;
  }

  uploadImage(): void {
    if (!this.selectedFile) {
      this.uploadError.emit('Please select an image first');
      return;
    }

    if (!this.sourceLanguage || !this.targetLanguage) {
      this.uploadError.emit('Please select both source and target languages');
      return;
    }

    this.isUploading = true;

    this.comicService.uploadImage(this.selectedFile, this.sourceLanguage, this.targetLanguage)
      .subscribe({
        next: (response: ProcessResponse) => {
          this.isUploading = false;
          this.imageUploaded.emit(response);
        },
        error: (error) => {
          this.isUploading = false;
          this.uploadError.emit('Failed to upload image: ' + error.message);
        }
      });
  }

  removeFile(): void {
    this.selectedFile = null;
  }

  getFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  onLanguagesSelected(languages: { source: string, target: string }): void {
    this.sourceLanguage = languages.source;
    this.targetLanguage = languages.target;
  }

  onSettingsChange(newSettings: TranslationSettings): void {
    this.settings = newSettings;
  }

  onFileRemoved(): void {
    this.removeFile();
  }
}
