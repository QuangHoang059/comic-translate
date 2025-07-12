# Comic Translate - Dependency Injection Architecture

## Tổng quan

Hệ thống đã được thiết kế lại theo pattern **Dependency Injection** sử dụng `dependency_injector` để quản lý các dependencies và configuration một cách có tổ chức.

## Cấu trúc mới

### 1. Container (`container/app_container.py`)

Container chính quản lý tất cả dependencies:

```python
class AppContainer(containers.DeclarativeContainer):
    # Configuration
    config = providers.Configuration()

    # Detection module
    detection_processor = providers.Singleton(TextBlockDetectorProcessor, ...)

    # OCR module
    ocr_processor = providers.Singleton(OCRProcessor)

    # Translation module
    translator = providers.Factory(Translator, ...)

    # Inpainting module
    inpainter = providers.Singleton(...)

    # Rendering module
    text_renderer = providers.Singleton(TextRenderer, ...)

    # Pipeline controllers
    pipeline_controller = providers.Singleton(...)
    api_pipeline = providers.Singleton(...)
```

### 2. Configuration (`config/config.json`)

File config tập trung cho tất cả modules:

```json
{
  "detection": {
    "model": "RT-DETR-V2",
    "device": "cpu",
    "confidence_threshold": 0.3
  },
  "ocr": {
    "model": "Default",
    "device": "cpu",
    "expansion_percentage": 5
  },
  "translation": {
    "model": "GPT-4o",
    "device": "cpu",
    "temperature": 1.0
  },
  "inpainting": {
    "model": "lama",
    "device": "cpu"
  },
  "credentials": {
    "openai": { "api_key": "" },
    "google": { "api_key": "" }
  }
}
```

### 3. Controllers

#### API Pipeline Controller (`controller/api_pipeline_controller.py`)

Controller cho headless processing:

```python
class APIPipelineController:
    @inject
    def __init__(self, detection_processor, ocr_processor, translator, ...):
        # Dependencies được inject tự động

    def detect_blocks(self, image):
        return self.detection_processor.detect(image)

    def process_ocr(self, image, blk_list, source_lang):
        return self.ocr_processor.process(image, blk_list)

    def process_full_pipeline(self, image, source_lang, target_lang):
        # Process toàn bộ pipeline
```

### 4. API Router (`api/router/api.py`)

Router sử dụng dependency injection:

```python
@router.post("/detect-blocks/{image_id}")
@inject
async def detect_blocks(
    image_id: str,
    pipeline: APIPipelineController = Provide[AppContainer.api_pipeline]
):
    blk_list = pipeline.detect_blocks(image)
    return ProcessResponse(...)
```

## Lợi ích của Architecture mới

### 1. **Separation of Concerns**

- Configuration tách biệt khỏi business logic
- Mỗi module có trách nhiệm riêng biệt
- Dễ test và maintain

### 2. **Dependency Management**

- Dependencies được quản lý tập trung
- Tự động inject dependencies
- Dễ thay đổi implementation

### 3. **Configuration Management**

- Config tập trung trong file JSON
- Dễ thay đổi settings mà không cần code
- Environment-specific configs

### 4. **Testability**

- Dễ mock dependencies cho testing
- Unit tests độc lập
- Integration tests đơn giản

### 5. **Scalability**

- Dễ thêm modules mới
- Dễ thay đổi implementations
- Loose coupling giữa components

## Cách sử dụng

### 1. Khởi tạo Container

```python
from container.app_container import AppContainer

# Load config và wire dependencies
container = AppContainer()
AppContainer.load_config()
```

### 2. Sử dụng trong API

```python
@inject
def my_api_endpoint(
    pipeline: APIPipelineController = Provide[AppContainer.api_pipeline]
):
    result = pipeline.process_full_pipeline(image, source_lang, target_lang)
    return result
```

### 3. Sử dụng trong UI

```python
@inject
def my_ui_function(
    controller: ComicTranslateControler = Provide[AppContainer.pipeline_controller]
):
    controller.detect_blocks()
```

### 4. Thêm Module mới

1. Tạo module class
2. Thêm provider vào container
3. Wire dependencies
4. Sử dụng với @inject

## Migration từ Architecture cũ

### 1. **Configuration**

- Chuyển hardcoded configs sang `config/config.json`
- Sử dụng `AppContainer.config` để access

### 2. **Controllers**

- Thêm `@inject` decorator
- Inject dependencies thay vì create manually
- Sử dụng providers từ container

### 3. **API Endpoints**

- Thêm `@inject` decorator
- Inject pipeline controller
- Sử dụng pipeline methods

### 4. **Testing**

- Mock container providers
- Test individual components
- Integration tests với real container

## Best Practices

### 1. **Provider Types**

- `providers.Singleton`: Cho services cần share state
- `providers.Factory`: Cho objects cần tạo mới mỗi lần
- `providers.Configuration`: Cho config values

### 2. **Dependency Injection**

- Sử dụng `@inject` decorator
- Inject interfaces thay vì concrete classes
- Avoid circular dependencies

### 3. **Configuration**

- Validate config values
- Provide defaults
- Environment-specific configs

### 4. **Error Handling**

- Handle missing dependencies
- Validate injected objects
- Graceful degradation

## Troubleshooting

### 1. **Circular Dependencies**

- Refactor để tránh circular imports
- Sử dụng interfaces
- Split large modules

### 2. **Missing Dependencies**

- Check provider definitions

- Check import paths

### 3. **Configuration Issues**

- Validate JSON syntax
- Check config paths
- Verify default values

## Future Enhancements

### 1. **Environment-specific Configs**

```python
# config/dev.json, config/prod.json
AppContainer.load_config(f"config/{os.getenv('ENV', 'dev')}.json")
```

### 2. **Dynamic Configuration**

```python
# Hot reload config
container.config.from_dict(new_config)
```

### 3. **Health Checks**

```python
# Check all dependencies
container.detection_processor().health_check()
```

### 4. **Metrics & Monitoring**

```python
# Track dependency usage
container.detection_processor().get_metrics()
```
