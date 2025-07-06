const fs = require("fs")
const fetch = require("node-fetch")
;(async () => {
  const res = await fetch("https://zenquotes.io/api/random")
  const data = await res.json()
  const quote = data[0].q
  const author = data[0].a

  const date = new Date()
  const dateStr = date.toLocaleDateString("en-IN", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  })

  // Using timestamp approach for truly live time
  const newContent = `## 🌟 Quote of the Day

💬 "${quote}"  — ${author}

📅 **Date :** ${dateStr}  

🕒 **Live Time :** <img src="https://img.shields.io/badge/dynamic/json?color=brightgreen&label=IST&query=%24.formatted&url=http%3A//worldtimeapi.org/api/timezone/Asia/Kolkata&style=for-the-badge&cacheSeconds=1&t=${Date.now()}" />

*⚡ Refreshes automatically when you view this page*`

  const readme = fs.readFileSync("README.md", "utf-8")
  const updated = readme.replace(
    /<!--START_SECTION:quote-->[\s\S]*<!--END_SECTION:quote-->/,
    `<!--START_SECTION:quote-->${newContent}<!--END_SECTION:quote-->`,
  )

  fs.writeFileSync("README.md", updated)
})()
