const fs = require("fs");
const fetch = require("node-fetch");

(async () => {
  const res = await fetch("https://api.quotable.io/random?tags=motivational|inspirational");
  const data = await res.json();

  const quote = data.content;
  const author = data.author;

  const date = new Date();
  const dateStr = date.toLocaleDateString("en-IN", { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  const timeStr = date.toLocaleTimeString("en-IN", { hour: '2-digit', minute: '2-digit' });

  const newContent = `
## 🌟 Quote of the Day

📅 Date: ${dateStr}  
🕒 Time: ${timeStr} IST  
💬 "${quote}"  
— ${author}
`;

  const readme = fs.readFileSync("README.md", "utf-8");
  const updated = readme.replace(
    /<!--START_SECTION:quote-->[\s\S]*<!--END_SECTION:quote-->/,
    `<!--START_SECTION:quote-->${newContent}<!--END_SECTION:quote-->`
  );

  fs.writeFileSync("README.md", updated);
})();
