import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface TranslationSettings {
  useGpu: boolean;
  extraContext: string;
  preserveFormatting: boolean;
  detectVerticalText: boolean;
  confidenceThreshold: number;
}

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})
export class SettingsComponent {
  @Input() settings: TranslationSettings = {
    useGpu: true,
    extraContext: '',
    preserveFormatting: true,
    detectVerticalText: true,
    confidenceThreshold: 0.7
  };
  
  @Output() settingsChange = new EventEmitter<TranslationSettings>();
  
  isExpanded: boolean = false;

  toggleExpanded(): void {
    this.isExpanded = !this.isExpanded;
  }

  onSettingChange(): void {
    this.settingsChange.emit({ ...this.settings });
  }

  resetToDefaults(): void {
    this.settings = {
      useGpu: true,
      extraContext: '',
      preserveFormatting: true,
      detectVerticalText: true,
      confidenceThreshold: 0.7
    };
    this.onSettingChange();
  }

  getConfidenceLabel(value: number): string {
    if (value < 0.3) return 'Very Low';
    if (value < 0.5) return 'Low';
    if (value < 0.7) return 'Medium';
    if (value < 0.9) return 'High';
    return 'Very High';
  }
}
