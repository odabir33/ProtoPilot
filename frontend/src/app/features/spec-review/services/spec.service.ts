import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class SpecService {
  readonly spec = signal<any>({});

  setSpec(spec: any): void {
    this.spec.set(spec);
  }

  updateSection(section: string, value: any): void {
    this.spec.update(current => ({ ...current, [section]: value }));
  }

  clearSpec(): void {
    this.spec.set({});
  }
}
