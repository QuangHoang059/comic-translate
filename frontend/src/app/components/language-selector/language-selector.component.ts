import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-language-selector',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './language-selector.component.html',
  styleUrls: ['./language-selector.component.css']
})
export class LanguageSelectorComponent {
  @Input() sourceLanguage: string = '';
  @Input() targetLanguage: string = '';
  @Input() supportedLanguages: string[] = [];
  @Input() disabled: boolean = false;

  @Output() sourceLanguageChange = new EventEmitter<string>();
  @Output() targetLanguageChange = new EventEmitter<string>();
  @Output() languagesSelected = new EventEmitter<{ source: string, target: string }>();

  onSourceLanguageChange(event: any): void {
    var language = event.target.value;
    this.sourceLanguage = language;
    this.sourceLanguageChange.emit(language);
    this.emitLanguagesSelected();
  }

  onTargetLanguageChange(event: any): void {
    var language = event.target.value;
    this.targetLanguage = language;
    this.targetLanguageChange.emit(language);
    this.emitLanguagesSelected();
  }

  private emitLanguagesSelected(): void {
    if (this.sourceLanguage && this.targetLanguage) {
      this.languagesSelected.emit({
        source: this.sourceLanguage,
        target: this.targetLanguage
      });
    }
  }

  swapLanguages(): void {
    if (this.disabled) return;

    const temp = this.sourceLanguage;
    this.sourceLanguage = this.targetLanguage;
    this.targetLanguage = temp;

    this.sourceLanguageChange.emit(this.sourceLanguage);
    this.targetLanguageChange.emit(this.targetLanguage);
    this.emitLanguagesSelected();
  }

  getLanguageFlag(language: string): string {
    const flagMap: { [key: string]: string } = {
      'English': '🇺🇸',
      'Japanese': '🇯🇵',
      'Korean': '🇰🇷',
      'Chinese (Simplified)': '🇨🇳',
      'Chinese (Traditional)': '🇹🇼',
      'Vietnamese': '🇻🇳',
      'French': '🇫🇷',
      'German': '🇩🇪',
      'Spanish': '🇪🇸',
      'Italian': '🇮🇹',
      'Portuguese': '🇵🇹',
      'Russian': '🇷🇺',
      'Arabic': '🇸🇦',
      'Thai': '🇹🇭'
    };
    return flagMap[language] || '🌍';
  }
}
