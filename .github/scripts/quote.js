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

  const newContent = `## 🌟 Quote of the Day

💬 "${quote}"  — ${author}

📅 **Date :** ${dateStr}  

🕒 **Current Time :** ![Time](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=IST&query=%24.time&url=http%3A%2F%2Fworldclockapi.com%2Fapi%2Fjson%2Fasia%2Fkolkata&style=for-the-badge&cacheSeconds=1)`

  const readme = fs.readFileSync("README.md", "utf-8")
  const updated = readme.replace(
    /<!--START_SECTION:quote-->[\s\S]*<!--END_SECTION:quote-->/,
    `<!--START_SECTION:quote-->${newContent}<!--END_SECTION:quote-->`,
  )

  fs.writeFileSync("README.md", updated)
})()
