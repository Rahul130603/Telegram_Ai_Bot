from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf" / "instagram_facebook_bot_setup_thanglish.pdf"

NAVY = colors.HexColor("#172554")
BLUE = colors.HexColor("#2563EB")
SKY = colors.HexColor("#EAF2FF")
GREEN = colors.HexColor("#15803D")
GREEN_BG = colors.HexColor("#ECFDF3")
AMBER = colors.HexColor("#B45309")
AMBER_BG = colors.HexColor("#FFF7E6")
RED = colors.HexColor("#B42318")
RED_BG = colors.HexColor("#FFF1F0")
SLATE = colors.HexColor("#334155")
MUTED = colors.HexColor("#64748B")
LINE = colors.HexColor("#D7E0EA")
PAPER = colors.HexColor("#F8FAFC")
WHITE = colors.white


styles = getSampleStyleSheet()
TITLE = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=27,
    leading=32,
    textColor=NAVY,
    alignment=TA_LEFT,
    spaceAfter=8,
)
SUBTITLE = ParagraphStyle(
    "Subtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=12,
    leading=18,
    textColor=SLATE,
)
H1 = ParagraphStyle(
    "H1Custom",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=19,
    leading=23,
    textColor=NAVY,
    spaceBefore=2,
    spaceAfter=10,
)
H2 = ParagraphStyle(
    "H2Custom",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=17,
    textColor=BLUE,
    spaceBefore=8,
    spaceAfter=5,
)
BODY = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=10.2,
    leading=15,
    textColor=SLATE,
    spaceAfter=6,
)
SMALL = ParagraphStyle(
    "SmallCustom",
    parent=BODY,
    fontSize=8.4,
    leading=12,
    textColor=MUTED,
)
STEP_TITLE = ParagraphStyle(
    "StepTitle",
    parent=H2,
    fontSize=13.5,
    leading=17,
    textColor=NAVY,
    spaceBefore=0,
    spaceAfter=3,
)
CODE = ParagraphStyle(
    "CodeCustom",
    parent=BODY,
    fontName="Courier",
    fontSize=8.5,
    leading=12,
    textColor=colors.HexColor("#E2E8F0"),
    leftIndent=0,
    rightIndent=0,
    spaceAfter=0,
)
CHECK = ParagraphStyle(
    "CheckCustom",
    parent=BODY,
    fontSize=9.6,
    leading=14,
    leftIndent=15,
    firstLineIndent=-15,
)


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def p(text: str, style: ParagraphStyle = BODY) -> Paragraph:
    return Paragraph(text, style)


def code(lines: str) -> Table:
    body = "<br/>".join(esc(line) if line else "&nbsp;" for line in lines.strip("\n").splitlines())
    table = Table([[Paragraph(body, CODE)]], colWidths=[166 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#1E293B")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def callout(title: str, text: str, kind: str = "info") -> Table:
    palette = {
        "info": (BLUE, SKY),
        "ok": (GREEN, GREEN_BG),
        "warn": (AMBER, AMBER_BG),
        "danger": (RED, RED_BG),
    }
    accent, background = palette[kind]
    title_style = ParagraphStyle("CalloutTitle", parent=BODY, fontName="Helvetica-Bold", textColor=accent, spaceAfter=2)
    table = Table(
        [[Paragraph(esc(title), title_style), Paragraph(text, BODY)]],
        colWidths=[34 * mm, 127 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("LINEBEFORE", (0, 0), (0, -1), 4, accent),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def step(number: int, title: str, body: str) -> Table:
    badge = Table([[p(str(number), ParagraphStyle("Badge", parent=BODY, fontName="Helvetica-Bold", fontSize=13, textColor=WHITE, alignment=TA_CENTER, leading=18))]], colWidths=[12 * mm], rowHeights=[9 * mm])
    badge.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BLUE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    right = [p(title, STEP_TITLE), p(body, BODY)]
    table = Table([[badge, right]], colWidths=[16 * mm, 145 * mm])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def checklist(text: str) -> Paragraph:
    return p(f"<font color='#15803D'><b>[ OK ]</b></font> {text}", CHECK)


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 14 * mm, width, 14 * mm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(WHITE)
    canvas.drawString(20 * mm, height - 9 * mm, "Telegram AI Bot - Social Media Setup")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 10 * mm, "Thanglish beginner guide | Secrets-ai yaarukkum share pannatheenga")
    canvas.drawRightString(width - 20 * mm, 10 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(20 * mm, 14 * mm, width - 20 * mm, 14 * mm)
    canvas.restoreState()


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=22 * mm,
        leftMargin=22 * mm,
        topMargin=22 * mm,
        bottomMargin=20 * mm,
        title="Instagram and Facebook Bot Setup - Thanglish Guide",
        author="Codex",
        subject="Telegram AI bot social publishing setup",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="guide", frames=[frame], onPage=header_footer)])

    story = []
    story += [Spacer(1, 13 * mm), p("Instagram + Facebook<br/>Bot Setup Guide", TITLE)]
    story += [p("Student-friendly Thanglish step-by-step process", SUBTITLE), Spacer(1, 8 * mm)]

    summary = Table(
        [
            [p("Goal", H2), p("Telegram bot-la image create panni, Instagram/Facebook select panni, confirm kudutha post publish aaganum.", BODY)],
            [p("Project", H2), p("D:\\Ai_Agent\\telegram-ai-bot\\backend", BODY)],
            [p("Important", H2), p("Indha project safety-kaga Preview -> Confirm Publish mudinja piraguthaan real post podum.", BODY)],
        ],
        colWidths=[35 * mm, 126 * mm],
    )
    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                ("GRID", (0, 0), (-1, -1), 0.6, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story += [summary, Spacer(1, 8 * mm)]
    story += [callout("4 main values", "<b>Instagram token</b> + <b>Instagram account ID</b> + <b>public HTTPS URL</b> + <b>project encryption key</b>.", "info")]
    story += [Spacer(1, 7 * mm), p("Full flow - one line-la", H1)]
    story += [code("Instagram Professional Account\n        |\nMeta Developer App -> Token + Instagram ID\n        |\nBackend + Cloudflare public URL\n        |\nTelegram bot -> Generate -> Select -> Confirm -> Publish")]
    story += [PageBreak()]

    story += [p("Part 1 - Start panna munnaadi", H1)]
    story += [step(1, "Accounts ready pannunga", "Oru Facebook personal login, oru Facebook Page, mattrum oru Instagram account venum. Instagram account-ai <b>Business</b> allathu <b>Creator</b> account-a maathunga.")]
    story += [p("Instagram app-la:", H2)]
    for item in [
        "Profile -> Menu -> Settings and activity",
        "Account type and tools -> Switch to professional account",
        "Business allathu Creator select pannunga",
        "Mudinja varaikkum Facebook Page-oda link pannunga",
    ]:
        story += [checklist(item)]
    story += [Spacer(1, 3 * mm), callout("Remember", "Personal Instagram account-ai official publishing API use panni post panna mudiyathu. Professional account required.", "warn")]
    story += [Spacer(1, 6 * mm), step(2, "Meta Developer App create pannunga", "Browser-la <b>developers.facebook.com/apps</b> open pannunga. Login -> My Apps -> Create App. Business-related use case/app type select panni app create pannunga.")]
    story += [p("App create aanadhum:", H2)]
    for item in [
        "Instagram product/use case add pannunga",
        "Instagram -> API Setup with Instagram Login open pannunga",
        "Unga Instagram Professional account-ai connect pannunga",
    ]:
        story += [checklist(item)]
    story += [callout("Dashboard labels", "Meta dashboard button names konjam maaralaam. Aana thevaiyana section: <b>Instagram API with Instagram Login</b>.", "info")]
    story += [PageBreak()]

    story += [p("Part 2 - Instagram keys edukkardhu", H1)]
    story += [step(3, "INSTAGRAM_ACCESS_TOKEN generate pannunga", "Meta app-oda Instagram API Setup page-la <b>Generate Access Token</b> click pannunga. Instagram login/authorization complete pannunga.")]
    story += [p("Minimum publishing permissions:", H2)]
    story += [code("instagram_business_basic\ninstagram_business_content_publish")]
    story += [Spacer(1, 3 * mm), p("Generate aana long secret value-ai copy panni .env-la podunga:", BODY)]
    story += [code("INSTAGRAM_ACCESS_TOKEN=IGAAxxxxxxxxxxxxxxxx")]
    story += [Spacer(1, 4 * mm), callout("Secret", "Indha token-ai screenshot, GitHub, WhatsApp group, email allathu public chat-la share pannatheenga.", "danger")]
    story += [Spacer(1, 6 * mm), step(4, "INSTAGRAM_BUSINESS_ACCOUNT_ID edunga", "Idhu Instagram username illa. Idhu Instagram API use pannura numeric user/account ID.")]
    story += [p("Token kidaicha piragu indha URL-ai Postman/browser-la use pannalaam:", BODY)]
    story += [code("https://graph.instagram.com/v21.0/me\n  ?fields=id,username\n  &access_token=YOUR_ACCESS_TOKEN")]
    story += [p("Response example:", H2)]
    story += [code('{\n  "id": "17841400000000000",\n  "username": "my_business_name"\n}')]
    story += [p("Response-la irukkura <b>id</b> value-ai .env-la podunga:", BODY)]
    story += [code("INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000")]
    story += [callout("ID confusion", "Instagram Account ID enbadhu username, Facebook Page ID, Meta App ID kidaiyaadhu. Correct value usually 178... pola long numeric ID-a irukkum.", "warn")]
    story += [PageBreak()]

    story += [p("Part 3 - Public image URL setup", H1)]
    story += [step(5, "Backend start pannunga", "Meta server unga generated image-ai internet-la download panna vendum. First local backend port 8000-la run aaganum.")]
    story += [code("cd D:\\Ai_Agent\\telegram-ai-bot\\backend\n.\\scripts\\run.ps1")]
    story += [Spacer(1, 5 * mm), step(6, "Cloudflare Tunnel start pannunga", "Pudhu PowerShell window open panni indha command run pannunga. Indha window close panna koodathu.")]
    story += [code("cloudflared tunnel --url http://127.0.0.1:8000")]
    story += [p("Output-la ippadi oru public HTTPS URL varum:", BODY)]
    story += [code("https://happy-tree-example.trycloudflare.com")]
    story += [p("Adhai .env-la podunga:", BODY)]
    story += [code("SOCIAL_PUBLIC_BASE_URL=https://happy-tree-example.trycloudflare.com")]
    story += [Spacer(1, 4 * mm), callout("Very important", "<b>localhost</b>, 127.0.0.1, http URL work aagathu. <b>https</b> public URL mattum use pannunga. URL-kku quotes/backticks thevai illa.", "danger")]
    story += [Spacer(1, 4 * mm), callout("Quick Tunnel", "cloudflared restart panna trycloudflare URL maaralaam. Appo .env public URL update panni backend-ai restart pannunga.", "warn")]
    story += [PageBreak()]

    story += [p("Part 4 - SOCIAL_TOKEN_KEY", H1)]
    story += [step(7, "Project encryption key generate pannunga", "Indha key Meta-kitta irundhu varaadhu. Project script automatic-a generate panni .env-la safe-a ezhuthum.")]
    story += [code("cd D:\\Ai_Agent\\telegram-ai-bot\\backend\npython scripts/generate_social_key.py --write-env")]
    story += [p("Success output:", H2)]
    story += [code("SOCIAL_TOKEN_KEY written privately to .env")]
    story += [p("Validate panna:", H2)]
    story += [code("python scripts/generate_social_key.py --check")]
    story += [p("Expected:", BODY), code("SOCIAL_TOKEN_KEY is valid")]
    story += [Spacer(1, 4 * mm), callout("Why needed?", "Facebook OAuth token madhiri sensitive connections database-la encrypt panni save panna SOCIAL_TOKEN_KEY use aagum.", "info")]
    story += [Spacer(1, 4 * mm), callout("Do not change", "Later indha key-ai random-a maathatheenga. Change pannina already saved encrypted connections read panna mudiyama pogalaam.", "warn")]
    story += [Spacer(1, 7 * mm), p("Ippo 4 main values ready", H1)]
    values = [
        [p("Variable", ParagraphStyle("TH", parent=BODY, fontName="Helvetica-Bold", textColor=WHITE)), p("Enga irundhu?", ParagraphStyle("TH2", parent=BODY, fontName="Helvetica-Bold", textColor=WHITE))],
        [p("INSTAGRAM_ACCESS_TOKEN", SMALL), p("Meta -> Instagram API Setup -> Generate Access Token", SMALL)],
        [p("INSTAGRAM_BUSINESS_ACCOUNT_ID", SMALL), p("Graph API /me response-la id", SMALL)],
        [p("SOCIAL_PUBLIC_BASE_URL", SMALL), p("cloudflared kudukkura https URL", SMALL)],
        [p("SOCIAL_TOKEN_KEY", SMALL), p("Project generate_social_key.py script", SMALL)],
    ]
    table = Table(values, colWidths=[63 * mm, 98 * mm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.5, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story += [table, PageBreak()]

    story += [p("Part 5 - Facebook connect pannardhu", H1)]
    story += [step(8, "Facebook App ID + Secret edunga", "Meta Developer App -> <b>App Settings -> Basic</b> open pannunga. Anga irukkura App ID mattrum App Secret-ai copy pannunga.")]
    story += [code("FACEBOOK_APP_ID=your_meta_app_id\nFACEBOOK_APP_SECRET=your_meta_app_secret")]
    story += [Spacer(1, 4 * mm), callout("Secret", "App Secret-ai public-a share pannatheenga. Idhu password madhiri.", "danger")]
    story += [Spacer(1, 5 * mm), step(9, "Facebook callback URL register pannunga", "Meta app-oda Facebook Login settings-la indha exact Valid OAuth Redirect URI add pannunga.")]
    story += [code("https://YOUR-PUBLIC-HOST/auth/facebook/callback")]
    story += [p("Example:", BODY)]
    story += [code("https://happy-tree-example.trycloudflare.com/auth/facebook/callback")]
    story += [p("Bot request panna vendiya permissions:", H2)]
    story += [code("pages_show_list\npages_read_engagement\npages_manage_posts\ninstagram_basic\ninstagram_content_publish")]
    story += [Spacer(1, 4 * mm), callout("Development mode", "App Admin/Developer/Tester accounts mattum testing-la work aagalaam. Public users-kku Live mode, App Review, Advanced Access allathu Business Verification thevai padalaam.", "warn")]
    story += [Spacer(1, 5 * mm), p("Telegram-la Facebook connect:", H2)]
    story += [code("/connect facebook")]
    story += [p("Bot kudukkura link open -> Facebook login -> Page permissions allow -> callback success.", BODY)]
    story += [PageBreak()]

    story += [p("Part 6 - Final .env + testing", H1)]
    story += [step(10, "Final values fill panni restart pannunga", "backend/.env file-la placeholders illama real values podunga. Example keezha irukku; example values-ai copy pannatheenga.")]
    story += [code("INSTAGRAM_LOGIN_FLOW=instagram\nINSTAGRAM_ACCESS_TOKEN=IGAA_your_real_token\nINSTAGRAM_BUSINESS_ACCOUNT_ID=1784_your_real_id\n\nSOCIAL_PUBLIC_BASE_URL=https://your-host.trycloudflare.com\nSOCIAL_TOKEN_KEY=generated_key_already_written\n\nFACEBOOK_APP_ID=your_real_app_id\nFACEBOOK_APP_SECRET=your_real_app_secret")]
    story += [Spacer(1, 4 * mm), p("Backend restart panna piragu checks:", H2)]
    story += [code("cd D:\\Ai_Agent\\telegram-ai-bot\\backend\npython scripts/check_instagram.py\npython scripts/check_social_oauth.py")]
    story += [p("Telegram test flow:", H2)]
    test_steps = [
        "Bot-kku /status anuppunga.",
        "Facebook connect illana /connect facebook anuppunga.",
        "Example: /image coffee shop offer poster anuppunga.",
        "Generated image vandhadhum Instagram allathu Facebook select pannunga.",
        "Preview correct-a irundha Confirm Publish click pannunga.",
        "Success message/permalink vandhucha check pannunga.",
    ]
    for index, item in enumerate(test_steps, 1):
        story += [p(f"<b>{index}.</b> {item}", CHECK)]
    story += [callout("Publish rule", "Platform select pannadhu mattum post illa. <b>Confirm Publish</b> mudinja piraguthaan real social post create aagum.", "ok")]
    story += [PageBreak()]

    story += [p("Troubleshooting - common problems", H1)]
    problems = [
        ("Instagram token/account missing", "Token and numeric account ID rendu values-um .env-la irukka check pannunga. Backend restart pannunga."),
        ("Instagram authentication failed", "Token expire/revoke aagirukkalaam; correct Instagram Login token and correct account ID use pannunga."),
        ("Public media URL error", "cloudflared run aagudha, current https URL .env-la same-a irukka, backend port 8000-la run aagudha check pannunga."),
        ("Facebook callback mismatch", "Meta dashboard redirect URI exact-a SOCIAL_PUBLIC_BASE_URL + /auth/facebook/callback match aaganum."),
        ("No managed Facebook Pages", "Login pannura Facebook user-kku Page full control/content permission irukka check pannunga."),
        ("Permissions error", "Correct scopes approve pannunga. Public users-na App Review/Advanced Access thevai padalaam."),
        ("Restart-ku apram connection poiduthu", "SOCIAL_TOKEN_KEY valid-a irukka; key-ai maathala; database path writable-a irukka check pannunga."),
    ]
    rows = [[p("Problem", ParagraphStyle("PH", parent=BODY, fontName="Helvetica-Bold", textColor=WHITE)), p("Enna check pannanum?", ParagraphStyle("PH2", parent=BODY, fontName="Helvetica-Bold", textColor=WHITE))]]
    rows += [[p(a, SMALL), p(b, SMALL)] for a, b in problems]
    trouble = Table(rows, colWidths=[52 * mm, 109 * mm], repeatRows=1)
    trouble.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PAPER]), ("GRID", (0, 0), (-1, -1), 0.5, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story += [trouble, Spacer(1, 7 * mm)]
    story += [p("Final checklist", H1)]
    for item in [
        "Instagram Professional account ready",
        "Meta Developer app ready",
        "Instagram token + numeric account ID filled",
        "Backend and cloudflared running",
        "SOCIAL_PUBLIC_BASE_URL current-a irukku",
        "SOCIAL_TOKEN_KEY generated and valid",
        "Facebook App ID/Secret + callback configured",
        "Bot-la preview -> confirm test success",
    ]:
        story += [checklist(item)]
    story += [Spacer(1, 5 * mm), p("Official references", H2)]
    story += [p("Meta Apps: https://developers.facebook.com/apps/<br/>Meta Instagram API collection: https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api<br/>Project README: D:\\Ai_Agent\\telegram-ai-bot\\README.md", SMALL)]

    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build()
