import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-left-panel',
  standalone: true,
  templateUrl: './left-panel.html',
  styleUrl: './left-panel.css'
})
export class LeftPanelComponent {

  @Input() spec: any;
  @Input() selectedSection: string = '';
  @Output() sectionSelected = new EventEmitter<string>();

  get sections(): string[] {
    return Object.keys(this.spec);
  }

  selectSection(section: string) {
    this.sectionSelected.emit(section);
  }

  toTitleCase(str: string): string {
    return str.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  }

}