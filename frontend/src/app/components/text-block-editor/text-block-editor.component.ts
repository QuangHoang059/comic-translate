import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TextBlockData } from '../../services/comic-translate.service';

@Component({
  selector: 'app-text-block-editor',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './text-block-editor.component.html',
  styleUrls: ['./text-block-editor.component.css']
})
export class TextBlockEditorComponent {
  @Input() blocks: TextBlockData[] = [];
  @Input() imageUrl: string = '';
  @Input() readonly: boolean = false;
  
  @Output() blocksChange = new EventEmitter<TextBlockData[]>();
  @Output() blockSelected = new EventEmitter<TextBlockData>();

  selectedBlockId: string | null = null;
  editingBlockId: string | null = null;
  showOriginalText: boolean = true;

  selectBlock(block: TextBlockData): void {
    this.selectedBlockId = block.id;
    this.blockSelected.emit(block);
  }

  startEditing(block: TextBlockData): void {
    if (this.readonly) return;
    this.editingBlockId = block.id;
  }

  stopEditing(): void {
    this.editingBlockId = null;
    this.emitBlocksChange();
  }

  updateBlockText(block: TextBlockData, newText: string): void {
    block.text = newText;
    this.emitBlocksChange();
  }

  updateBlockTranslation(block: TextBlockData, newTranslation: string): void {
    block.translation = newTranslation;
    this.emitBlocksChange();
  }

  deleteBlock(blockToDelete: TextBlockData): void {
    if (this.readonly) return;
    
    const index = this.blocks.findIndex(block => block.id === blockToDelete.id);
    if (index > -1) {
      this.blocks.splice(index, 1);
      this.emitBlocksChange();
    }
  }

  private emitBlocksChange(): void {
    this.blocksChange.emit([...this.blocks]);
  }

  getBlockPosition(block: TextBlockData): string {
    const [x1, y1, x2, y2] = block.xyxy;
    return `(${x1}, ${y1}) - (${x2}, ${y2})`;
  }

  getBlockSize(block: TextBlockData): string {
    const [x1, y1, x2, y2] = block.xyxy;
    const width = x2 - x1;
    const height = y2 - y1;
    return `${width} × ${height}px`;
  }

  getBlockAngle(block: TextBlockData): string {
    return `${block.angle.toFixed(1)}°`;
  }

  toggleTextDisplay(): void {
    this.showOriginalText = !this.showOriginalText;
  }

  hasText(block: TextBlockData): boolean {
    return !!(block.text && block.text.trim());
  }

  hasTranslation(block: TextBlockData): boolean {
    return !!(block.translation && block.translation.trim());
  }

  getBlockStatus(block: TextBlockData): 'empty' | 'text-only' | 'translated' {
    if (!this.hasText(block)) return 'empty';
    if (!this.hasTranslation(block)) return 'text-only';
    return 'translated';
  }

  getStatusIcon(status: string): string {
    switch (status) {
      case 'empty': return '⚪';
      case 'text-only': return '🟡';
      case 'translated': return '🟢';
      default: return '⚪';
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'empty': return 'No text detected';
      case 'text-only': return 'Text detected, not translated';
      case 'translated': return 'Translated';
      default: return 'Unknown';
    }
  }
}
