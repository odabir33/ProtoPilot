import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LivePreviewComponent } from './live-preview.component';
import { CodeSandboxPreviewService } from '../../services/codesandbox-preview.service';

describe('LivePreviewComponent', () => {
  let component: LivePreviewComponent;
  let fixture: ComponentFixture<LivePreviewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LivePreviewComponent],
      providers: [CodeSandboxPreviewService]
    }).compileComponents();

    fixture = TestBed.createComponent(LivePreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
