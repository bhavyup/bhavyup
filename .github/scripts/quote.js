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

  // Get current IST time and format it
  const now = new Date()
  const istTime = now.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  })

  const newContent = `## 🌟 Quote of the Day

💬 "${quote}"  — ${author}

📅 **Date :** ${dateStr}  

🕒 **Current Time :** ![Time](https://img.shields.io/badge/IST-${encodeURIComponent(istTime)}-brightgreen?style=for-the-badge&logo=clock)

⏰ **Live Clock :** <img src="https://img.shields.io/badge/dynamic/json?color=blue&label=Live%20UTC&query=%24.utc_datetime&url=https%3A%2F%2Fworldtimeapi.org%2Fapi%2Ftimezone%2FUTC&style=flat-square&cacheSeconds=1&t=${Date.now()}" />`

  const readme = fs.readFileSync("README.md", "utf-8")
  const updated = readme.replace(
    /<!--START_SECTION:quote-->[\s\S]*<!--END_SECTION:quote-->/,
    `<!--START_SECTION:quote-->${newContent}<!--END_SECTION:quote-->`,
  )

  fs.writeFileSync("README.md", updated)
})()
