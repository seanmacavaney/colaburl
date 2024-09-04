## ColabURL

Colab URL Generator from Code

**Install:**

```bash
pip install colaburl
```

**Usage:**

```python
>>> import colaburl
>>> colaburl.code_url('''
... import my_module
... my_module.something()
... ''')
'https://colaburl.uk/aW1wb3J0IG15X21vZHVsZQpteV9tb2R1bGUuc29tZXRoaW5nKCk=.b64'
>>> colaburl.code_html('''
... import my_module
... my_module.something()
... ''')
'<a href="https://colaburl.uk/aW1wb3J0IG15X21vZHVsZQpteV9tb2R1bGUuc29tZXRoaW5nKCk=.b64" rel="nofollow" target="_blank" class="colaburl"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab" style="margin: 0; display: inline-block;" /></a>'
```
