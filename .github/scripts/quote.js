const fs = require("fs");
const fetch = require("node-fetch");

(async () => {
  const res = await fetch("https://zenquotes.io/api/random");
  const data = await res.json();

  const quote = data[0].q;
  const author = data[0].a;

  const date = new Date();
  const dateStr = date.toLocaleDateString("en-IN", {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  });
  const timeStr = date.toLocaleTimeString("en-IN", {
    hour: '2-digit', minute: '2-digit'
  });

  const newContent = `
## 🌟 Quote of the Day

📅 Date: ${dateStr}  
🕒 Time: ![Time](https://readme-time.vercel.app/api?timezone=Asia/Kolkata)  
💬 "${quote}"  
      \t — ${author}
`;

  const readme = fs.readFileSync("README.md", "utf-8");
  const updated = readme.replace(
    /<!--START_SECTION:quote-->[\s\S]*<!--END_SECTION:quote-->/,
    `<!--START_SECTION:quote-->${newContent}<!--END_SECTION:quote-->`
  );

  fs.writeFileSync("README.md", updated);
})();

