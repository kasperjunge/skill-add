---
description: A simple hello world slash command example
argument-hint: [name]
---

Say hello to the user. If they provided a name as an argument ($ARGUMENTS), greet them by name. Otherwise, just say "Hello, World!"

Respond with something like:

```
Hello, $ARGUMENTS! 👋

This greeting was triggered by the /hello-world slash command.
Slash commands are explicitly invoked by the user.
```

If no name was provided:

```
Hello, World! 👋

This greeting was triggered by the /hello-world slash command.
Try: /hello-world [your-name]
```

