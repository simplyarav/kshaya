import os
import re

path = r'ui\src\components\LandingPage.tsx'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(\"export default function LandingPage({ onEnter }) {\", \"export default function LandingPage({ onEnter }: { onEnter: () => void }) {\")
text = text.replace(\"import { useState, useEffect } from 'react';\", \"import React, { useState, useEffect } from 'react';\")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
