# ABC QUEST — בניית אפליקציית Android

פרויקט לימודי לילדים דוברי עברית: 26 אותיות באנגלית, משחקים, גביעים, קרדיטים, 15 דמויות ו־60 סקינים.

## הפקת APK באמצעות GitHub Actions

1. הורד מצ'אט ChatGPT את `ABC_QUEST_Android_v7_פרויקט_לבניית_APK.zip`.
2. במאגר זה לחץ **Add file → Upload files** והעלה את קובץ ה־ZIP בשלמותו **בלי לחלץ אותו**.
3. לחץ **Commit changes** והמתן לתהליך הבנייה בלשונית [Actions](../../actions/workflows/build-android-apk.yml). אפשר גם להפעיל **Run workflow** ידנית.
4. כשהתהליך **Build ABC QUEST Android APK** מסומן בירוק, פתח את ההרצה ובחר ב־**Artifacts → ABC_QUEST_v7_APK**.
5. הורד את קובץ הארטיפקט (ZIP), חלץ אותו; בתוכו נמצא **app-debug.apk**.
6. העבר את `app-debug.apk` לטלפון אנדרואיד, פתח דרך Files ואשר התקנה ממקור זה אם תתבקש.

**הערה:** כל שינוי במאגר מפעיל את תהליך הבנייה. עד להעלאת ארכיון פרויקט Android, הבנייה תיכשל בהודעת **Upload the Android project ZIP**. זו התנהגות צפויה.

הפרויקט מכיל WebView עם קובצי המשחק המוטמעים. האפליקציה נבנית ב־Java 17, Android SDK 35 ו־Gradle 8.9. APK בגרסת debug מיועד לבדיקה מקומית בלבד ולא לפרסום ב־Google Play.

**פרטיות:** אין להעלות נתוני התקדמות אישיים של ילדים. המאגר כרגע ציבורי. אפשר לשנות ל־Private ב־Settings → General → Danger Zone → Change repository visibility.
