import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-file-preview',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './file-preview.component.html',
  styleUrls: ['./file-preview.component.css']
})
export class FilePreviewComponent implements OnInit, OnDestroy {
  @Input() file: File | null = null;
  @Input() showDetails: boolean = true;
  @Input() allowRemove: boolean = true;
  @Input() maxPreviewSize: number = 300; // pixels
  
  @Output() fileRemoved = new EventEmitter<void>();
  @Output() fileClicked = new EventEmitter<File>();

  previewUrl: SafeUrl | null = null;
  isImageFile: boolean = false;
  fileSize: string = '';
  fileType: string = '';

  constructor(private sanitizer: DomSanitizer) {}

  ngOnInit(): void {
    if (this.file) {
      this.processFile();
    }
  }

  ngOnDestroy(): void {
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl as string);
    }
  }

  private processFile(): void {
    if (!this.file) return;

    this.isImageFile = this.file.type.startsWith('image/');
    this.fileSize = this.formatFileSize(this.file.size);
    this.fileType = this.getFileTypeDisplay(this.file.type);

    if (this.isImageFile) {
      this.createImagePreview();
    }
  }

  private createImagePreview(): void {
    if (!this.file) return;

    const url = URL.createObjectURL(this.file);
    this.previewUrl = this.sanitizer.bypassSecurityTrustUrl(url);
  }

  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  private getFileTypeDisplay(mimeType: string): string {
    const typeMap: { [key: string]: string } = {
      'image/jpeg': 'JPEG Image',
      'image/jpg': 'JPG Image',
      'image/png': 'PNG Image',
      'image/gif': 'GIF Image',
      'image/webp': 'WebP Image',
      'image/bmp': 'BMP Image',
      'image/svg+xml': 'SVG Image'
    };

    return typeMap[mimeType] || mimeType || 'Unknown';
  }

  onRemoveFile(): void {
    this.fileRemoved.emit();
  }

  onFileClick(): void {
    if (this.file) {
      this.fileClicked.emit(this.file);
    }
  }

  getFileIcon(): string {
    if (!this.file) return '📄';
    
    if (this.file.type.startsWith('image/')) {
      return '🖼️';
    }
    
    return '📄';
  }

  isFileSizeValid(): boolean {
    if (!this.file) return false;
    
    // 10MB limit
    const maxSize = 10 * 1024 * 1024;
    return this.file.size <= maxSize;
  }

  getFileSizeWarning(): string {
    if (!this.file) return '';
    
    const maxSize = 10 * 1024 * 1024;
    if (this.file.size > maxSize) {
      return 'File size exceeds 10MB limit';
    }
    
    return '';
  }
}
