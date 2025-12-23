{
    "name": "Report Logo Size - 100 Watt",
    "summary": "Customize company logo size in reports",
    "version": "18.0.1.0.0",
    "category": "Reporting",
    "author": "Ahmed Tarek",
    "license": "LGPL-3",
    "description": """
        Report Logo Size Customization - 100 Watt
        ==========================================
        This module customizes the company logo size in reports.
        
        Features:
        ---------
        * Larger logo dimensions: 5.3cm x 1.8cm (52.2mm x 150px)
        * Applied to all report layouts
        
    """,

    "depends": [
        "web",
        "base",
    ],

    "data": [],

    "assets": {
        "web.report_assets_common": [
            "nx_100_report_logo_size/static/src/css/report_logo.css",
        ],
    },

    "installable": True,
    "application": False,
}
