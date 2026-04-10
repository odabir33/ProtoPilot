import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LoaderComponent } from './loader.component';
import { LoaderService } from '../../services/loader.service';

describe('LoaderComponent', () => {
  let component: LoaderComponent;
  let fixture: ComponentFixture<LoaderComponent>;
  let loaderService: LoaderService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoaderComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(LoaderComponent);
    component = fixture.componentInstance;
    loaderService = TestBed.inject(LoaderService);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show loader when service starts', (done) => {
    loaderService.start();
    component.loaderState$.subscribe((state) => {
      if (state.isLoading) {
        expect(state.message).toBeTruthy();
        loaderService.stop();
        done();
      }
    });
  });

  it('should stop loader', (done) => {
    loaderService.start();
    setTimeout(() => {
      loaderService.stop();
      component.loaderState$.subscribe((state) => {
        expect(state.isLoading).toBeFalse();
        done();
      });
    }, 100);
  });
});
