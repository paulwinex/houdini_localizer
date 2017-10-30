# Houdini Localizer

Сборщик ресурсов для сцен Houdini

Автор: Ivan Larinin


### Install

1. Поместить модуль `houdini_localizer.py` в `PYTHONPATH`. Папример `HOUDINI_PATH/scripts/python`
2. Добавить новую кнопку на полку с таким кодом:

```python
import houdini_localizer
houdini_localizer.HoudiniLocalizer().selected_nodes()
```
