import { JsonPipe } from '@angular/common';
import { Component, inject, Input, OnChanges } from '@angular/core';
import { FormsModule } from '@angular/forms';import { MarkdownModule } from 'ngx-markdown';import { WizardService } from '../requirements/services/wizard-service';
import { catchError, of } from 'rxjs';

@Component({
  selector: 'app-right-panel',
  standalone: true,
  imports: [FormsModule, JsonPipe, MarkdownModule],
  templateUrl: './right-panel.html',
  styleUrl: './right-panel.css'
})
export class RightPanelComponent implements OnChanges {

  @Input() spec: any;
  @Input() selectedSection: string = '';
  @Input() mdText: string = '';
  @Input() isPreviewMode: boolean = false;

  isEditing: boolean = false;
  editedValue: string = '';
  editedArray: string[] = [];
  editedObjects: any[] = [];
  chatMessage: string = '';
  wizardService = inject(WizardService);

  constructor() {}

  ngOnChanges() {
    this.isEditing = false;
  }

  get selectedData() {
    return this.spec[this.selectedSection];
  }

  get isStringArray(): boolean {
    return Array.isArray(this.selectedData) && this.selectedData.every(item => typeof item === 'string');
  }

  get isObjectArray(): boolean {
    return Array.isArray(this.selectedData) && this.selectedData.length > 0 && typeof this.selectedData[0] === 'object' && !Array.isArray(this.selectedData[0]);
  }

  get isObject(): boolean {
    return typeof this.selectedData === 'object' && !Array.isArray(this.selectedData) && this.selectedData !== null;
  }

  getObjectKeys(obj: any): string[] {
    return Object.keys(obj);
  }

  toTitleCase(str: string): string {
    return str.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  }

  startEdit() {
    this.isEditing = true;
    const data = this.selectedData;
    const isString = typeof data === 'string';
    const isStringArray = this.isStringArray;
    const isObjectArray = this.isObjectArray;
    const isObject = this.isObject;

    if (isString) {
      this.editedValue = data;
    } else if (isStringArray) {
      this.editedArray = [...data];
    } else if (isObjectArray) {
      this.editedObjects = JSON.parse(JSON.stringify(data));
    } else if (isObject) {
      this.editedObjects = [JSON.parse(JSON.stringify(data))];
    } else {
      this.editedValue = JSON.stringify(data, null, 2);
    }
  }

  saveEdit() {
    try {
      const data = this.selectedData;
      const isString = typeof data === 'string';
      const isStringArray = this.isStringArray;
      const isObjectArray = this.isObjectArray;
      const isObject = this.isObject;

      if (isString) {
        this.spec[this.selectedSection] = this.editedValue;
      } else if (isStringArray) {
        this.spec[this.selectedSection] = this.editedArray;
      } else if (isObjectArray) {
        this.spec[this.selectedSection] = this.editedObjects;
      } else if (isObject) {
        this.spec[this.selectedSection] = this.editedObjects[0];
      } else {
        this.spec[this.selectedSection] = JSON.parse(this.editedValue);
      }
      this.isEditing = false;
    } catch (e) {
      alert('Invalid input');
    }
  }

  cancelEdit() {
    this.isEditing = false;
  }

  addItem() {
    this.editedArray.push('');
  }

  removeItem(index: number) {
    this.editedArray.splice(index, 1);
  }

  addObject() {
    const template = this.editedObjects.length > 0 ? {...this.editedObjects[0]} : {};
    Object.keys(template).forEach(k => template[k] = '');
    this.editedObjects.push(template);
  }

  removeObject(index: number) {
    this.editedObjects.splice(index, 1);
  }

  sendChatMessage() {
    if (this.chatMessage) {
      this.wizardService.sendMessage(this.chatMessage).pipe(catchError(err => {
                console.log('Error caught:', err);
                return of(null); // fallback value
              })).subscribe(response => {
        if (response) {
          // Update spec based on response
          console.log('Response received: ' + JSON.stringify(response));
        }
        this.chatMessage = '';
      });
    }
  }

}