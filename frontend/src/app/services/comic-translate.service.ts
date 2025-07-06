import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface TextBlockData {
  id: string;
  xyxy: number[];
  text?: string;
  translation?: string;
  angle: number;
}

export interface ProcessResponse {
  image_id: string;
  blocks: TextBlockData[];
  status: string;
}

export interface TranslationRequest {
  source_language: string;
  target_language: string;
  extra_context?: string;
  use_gpu: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ComicTranslateService {
  private apiUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) { }

  // Upload image
  uploadImage(file: File, sourceLanguage: string, targetLanguage: string): Observable<ProcessResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_language', sourceLanguage);
    formData.append('target_language', targetLanguage);

    return this.http.post<ProcessResponse>(`${this.apiUrl}/upload`, formData);
  }

  // Detect text blocks
  detectBlocks(imageId: string): Observable<ProcessResponse> {
    return this.http.post<ProcessResponse>(`${this.apiUrl}/detect-blocks/${imageId}`, {});
  }

  // OCR text from blocks
  ocrImage(imageId: string): Observable<ProcessResponse> {
    return this.http.post<ProcessResponse>(`${this.apiUrl}/ocr/${imageId}`, {});
  }

  // Translate text
  translateImage(imageId: string, request: TranslationRequest): Observable<ProcessResponse> {
    return this.http.post<ProcessResponse>(`${this.apiUrl}/translate/${imageId}`, request);
  }

  // Inpaint image
  inpaintImage(imageId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/inpaint/${imageId}`, {});
  }

  // Render final image
  renderImage(imageId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/render/${imageId}`, {});
  }

  // Get result image
  getResultImage(imageId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/result/${imageId}`, { responseType: 'blob' });
  }

  // Process all steps at once
  translateAll(imageId: string, request: TranslationRequest): Observable<ProcessResponse> {
    return this.http.post<ProcessResponse>(`${this.apiUrl}/translate-all/${imageId}`, request);
  }

  // Get supported languages
  getSupportedLanguages(): string[] {
    return [
      'English',
      'Japanese', 
      'Korean',
      'Chinese (Simplified)',
      'Chinese (Traditional)',
      'Vietnamese',
      'French',
      'German',
      'Spanish',
      'Italian',
      'Portuguese',
      'Russian',
      'Arabic',
      'Thai'
    ];
  }
}
