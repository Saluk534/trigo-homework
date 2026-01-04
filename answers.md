כיווני מחשבה: 

בדיקה אם פרומתיוס יודע לקבל מערך כרשימת טרגסט - נשלל כי הוא לא יודע 
בדיקה של פרויקט גיט בשם https://github.com/laixintao/prometheus-http-sd?tab=readme-ov-file#usage שיוכל לעשות זאת 
חוסר יכולת להתחבר לזה בגלל חשבון דוקר 

סקריפט פייתון ידני שירוץ על קונטיינר ספציפי של פייתון, ייגש כל 5 שניות לרשימת השרתים ויעדכן אותה בווליום שהוא קובץ גייסון 
הפרומיתיוס יסתכל גם הוא כל 5 שניות ויבדוק שינויים בקובץ 
וכך יהיה סנכרון ביניהם 
מבחינה אבטחתית: 
הקונטיינר היחיד שיש לו גישה חיצונית הוא הפרומתיוס בפורט 9090 , כל השאר עובדים בתקשורת פנימית בין קונטיינרים ברשת trigo-net
רציתי גם לשנות את היוזר שרץ בקונטיינר update_targets שלא יהיה רוט אלא משתמש עם פחות הרשאות 

חסרונות בשיטה שבחרתי: 
קונטיינר שחי תמיד וצורך משאבים למרות שהוא בפעולה פעם אחת ב5 שניות לסקריפט קצר , אם הייתי בסביבת ענן הייתי משתמש בstateless function  או כקרון גוב בסביבת קוברנטיס 

ככלל הייתי מעדיף להריץ את הסקריפט כקרון גוב על הקונטיינר update targets , אבל בגלל תקלת האינטרנט השארתי את זה עם sleep בסוף. 
הסיבה שהייתי מעדיף קרון גוב היא נוחות וקריאות בעיקר. 

בשביל להריץ את הסביבה יש להריץ docker compose up 
לגשת לlocalhost:9090  ולראות את הפרותיוס 

<div dir="rtl">

<h1>⚙️ סיכום תרגיל Prometheus ו־Python Updater</h1>

<h2>🧪 תהליך הבדיקה</h2>
<ul>
  <li><b>בדיקה ראשונה:</b> האם Prometheus יודע לקבל מערך טרגטים ישירות — ❌ נשלל (נדרש פורמט JSON ייעודי).</li>
  <li><b>בדיקה שנייה:</b> פרויקט GitHub
    <a href="https://github.com/laixintao/prometheus-http-sd?tab=readme-ov-file#usage">prometheus-http-sd</a>
    – נבדק כפתרון אפשרי, אך ❌ לא התחבר בשל בעיית חשבון Docker.
  </li>
</ul>

<h2>🐍 הסקריפט שפותח</h2>
<ul>
  <li>סקריפט Python בקונטיינר ייעודי.</li>
  <li>כל <b>5 שניות</b> ניגש ל־Flask (רשימת השרתים) ומעדכן <code>targets.json</code> בנפח משותף (Volume).</li>
  <li>Prometheus קורא את אותו קובץ דרך <code>file_sd_config</code> ומרענן גם הוא כל <b>5 שניות</b>.</li>
</ul>

<h2>🔐 שיקולי אבטחה</h2>
<ul>
  <li>הקונטיינר היחיד שחשוף החוצה: <b>Prometheus</b> (פורט 9090).</li>
  <li>שאר הקונטיינרים מתקשרים פנימית בלבד על רשת <code>trigo-net</code>.</li>
</ul>

<h2>👤 הרשאות והרצה</h2>
<ul>
  <li>הקונטיינר <code>update_targets</code> רץ כמשתמש לא־root (מינימום הרשאות).</li>
</ul>

<h2>⚠️ חסרונות</h2>
<ul>
  <li>קונטיינר ה־Updater “חי” תמיד, אף שהפעולה קצרה ומתרחשת כל 5 שניות.</li>
  <li>בענן היה עדיף <b>Stateless Function</b> או <b>CronJob בקוברנטיס</b>.</li>
</ul>

<h2>🧭 שיקולים תכנוניים</h2>
<ul>
  <li>העדפה ל־<b>CronJob</b> לקריאות ונוחות; בשל תקלת אינטרנט נבחר פתרון <code>sleep</code> זמני.</li>
</ul>

<h2>🚀 הפעלה</h2>
<ol>
  <li>להריץ: <code>docker compose up</code></li>
  <li>לגלוש ל־ <code>http://localhost:9090</code></li>
  <li>ב־<b>Targets</b> לוודא שכל היעדים מזוהים.</li>
</ol>

<h2>📚 סיכום</h2>
<ul>
  <li>Prometheus כנקודת ניטור יחידה החשופה החוצה.</li>
  <li>Updater מעדכן דינמית את רשימת היעדים.</li>
  <li>רשת פנימית מבודדת (<code>trigo-net</code>), והרשאות מצומצמות.</li>
</ul>

</div>


Dynamic Prometheus Target Updater
Overview

This project provides a dynamic way for Prometheus to discover targets without requiring manual configuration or service discovery integrations.
A lightweight Python container periodically fetches a list of servers and updates a JSON file shared with Prometheus via a Docker volume.
Prometheus is configured to read from this file every 5 seconds, effectively synchronizing its targets dynamically.

Background and Reasoning
Initial Considerations

Prometheus native configuration does not support defining targets as an array dynamically.

Attempted approach: using prometheus-http-sd
 — rejected due to Docker authentication issues.

Final Approach

A custom Python script runs inside a dedicated container (update_targets).

Every 5 seconds, it:

Fetches the current server list.

Updates a shared JSON file inside a Docker volume.

Prometheus also reads this file every 5 seconds, detecting any changes automatically.

Security Considerations

The only externally accessible container is Prometheus (port 9090).

All other containers communicate internally via the Docker network trigo-net.

The update_targets container runs as a non-root user to minimize privileges.

Limitations

The Python container runs continuously, consuming minimal but constant resources, even though it only performs work every 5 seconds.

In a cloud or Kubernetes environment, this would ideally run as a stateless function or a CronJob, triggered periodically instead of being persistent.

Design Decision

The current setup uses a sleep loop for simplicity due to connectivity issues.
However, the preferred method would be a cron-based execution for better readability and maintainability.

Usage

Run the environment:

docker compose up


Access Prometheus at:

http://localhost:9090


You should see your dynamically updated targets reflected automatically.