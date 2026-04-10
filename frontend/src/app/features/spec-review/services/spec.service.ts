import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class SpecService {
  readonly spec = signal<any>({});
  readonly nontech_artifacts_md = signal<Record<string, string> | null>(null);
  readonly technical_artifacts_md = signal<Record<string, string> | null>(null);

  setSpec(spec: any): void {
    this.spec.set(spec);
  }

  updateSection(section: string, value: any): void {
    this.spec.update(current => ({ ...current, [section]: value }));
  }

  clearSpec(): void {
    this.spec.set({});
  }

  setNontechArtifacts(artifacts: Record<string, string>): void {
    this.nontech_artifacts_md.set(artifacts);
  }

  setTechnicalArtifacts(artifacts: Record<string, string>): void {
    this.technical_artifacts_md.set(artifacts);
  }

  updateNontechArtifact(filename: string, content: string): void {
    this.nontech_artifacts_md.update(current => ({
      ...current,
      [filename]: content
    }));
  }

  updateTechnicalArtifact(filename: string, content: string): void {
    this.technical_artifacts_md.update(current => ({
      ...current,
      [filename]: content
    }));
  }

  clearArtifacts(): void {
    this.nontech_artifacts_md.set(null);
    this.technical_artifacts_md.set(null);
  }
}
