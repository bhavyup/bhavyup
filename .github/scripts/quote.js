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

  // Use a working time badge service
  const newContent = `## 🌟 Quote of the Day

💬 "${quote}"  — ${author}

📅 **Date :** ${dateStr}  

🕒 **Current Time :** ![Current Time](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=UTC%20Time&query=%24.datetime&url=https%3A%2F%2Fworldtimeapi.org%2Fapi%2Ftimezone%2FUTC&suffix=%20UTC)

⏰ **Your Local Time :** 
<img src="https://img.shields.io/badge/dynamic/json?color=blue&label=Local%20Time&query=$.datetime&url=https://worldtimeapi.org/api/timezone/Etc/UTC" id="local-time-badge">

<script>
document.getElementById('local-time-badge').src = 'https://img.shields.io/badge/Local%20Time-' + new Date().toLocaleString() + '-blue';
</script>`

  const readme = fs.readFileSync("README.md", "utf-8")
  const updated = readme.replace(
    /<!--START_SECTION:quote-->[\s\S]*<!--END_SECTION:quote-->/,
    `<!--START_SECTION:quote-->${newContent}<!--END_SECTION:quote-->`,
  )

  fs.writeFileSync("README.md", updated)
})()
