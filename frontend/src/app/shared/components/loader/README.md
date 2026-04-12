# Loader Service & Component

A reusable Angular loader service and component that displays a transparent overlay with a spinning animation and cycling messages.

## Usage

### Basic Usage

```typescript
import { Component, inject } from '@angular/core';
import { LoaderService } from '@app/shared/services/loader.service';

@Component({
  selector: 'app-my-component',
  standalone: true,
  template: `<button (click)="performAction()">Click me</button>`
})
export class MyComponent {
  private loaderService = inject(LoaderService);

  performAction() {
    this.loaderService.start();
    
    // Do some async work
    setTimeout(() => {
      this.loaderService.stop();
    }, 3000);
  }
}
```

### With Custom Messages

```typescript
performAction() {
  const customMessages = ['Generating artifacts...', 'Creating files...', 'Finalizing...'];
  this.loaderService.startWithMessages(customMessages);
  
  // Do async work
  someAsyncOperation().then(() => {
    this.loaderService.stop();
  });
}
```

### With Static Message

```typescript
performAction() {
  this.loaderService.showWithMessage('Processing your request...');
  
  // Do async work
  someAsyncOperation().then(() => {
    this.loaderService.stop();
  });
}
```

## Features

- **Transparent Overlay**: Prevents user interaction while loading
- **Animated Spinner**: Smooth CSS animation
- **Cycling Messages**: Default messages cycle every 1.5 seconds
- **Customizable**: Supports custom message sequences
- **Easy Control**: Simple start/stop functions

## Default Messages

- "Thinking..."
- "Almost there..."
- "Processing..."
- "Loading..."

## API

### `LoaderService`

#### Methods

- `start()`: Starts the loader with default messages
- `startWithMessages(messages: string[])`: Starts the loader with custom message sequence
- `stop()`: Stops the loader
- `showWithMessage(message: string)`: Shows loader with a single static message
- `getState()`: Returns current loader state

#### Observable

- `loaderState$`: Observable of type `LoaderState` containing `isLoading` boolean and `message` string
