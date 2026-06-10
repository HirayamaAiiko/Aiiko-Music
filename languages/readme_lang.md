# 🌍 Aiiko Music - Translation Guide

## 📝 How to Translate

1. **Duplicate the Base File**  
   Copy and paste the `base.json` file located in the `languages` folder and rename it to your target language code (for example, `jp.json` for japanese).

2. **Configure the Meta Header**  
   Open your newly created file and edit the beginning (before the text). Add the following header block so that the application's language selector knows how to display it nicely:

   ```json
   {
       "_meta": {
           "author": "Hirayama Ai",
           "version": "1.2",
           "language_name": "Español",
           "language_code": "es",
           "date": "2026-06-10"
       },
       
   }
   ```
   *(Make sure to update the values with your own author name, language name, and code!)*

3. **Translate the Strings**  
   Translate all the values to the **right** of the colon `:`.
   
   > ⚠️ **CRITICAL:** Leave the part to the **left** (the "key" in Spanish) entirely untouched. That is what the internal engine uses to find the text in the interface.

   **Correct Example:**
   ```json
   "Ajustes": "Configurações",
   "Canciones": "Músicas"
   ```

---

### 💡 A Note on Raw References

The translation system currently uses a raw reference mechanism. Because the base keys are written in Spanish, some knowledge of the base written language will be necessary to accurately interpret and translate the context. 

*This system will be modified and improved over time.*

