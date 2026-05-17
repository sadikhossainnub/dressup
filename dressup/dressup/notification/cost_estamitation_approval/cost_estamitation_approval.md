<p><!-- Subject: Approval Required: Cost Estimation – {{ doc.tech_pack_no or doc.name }} | Prepared by {{ doc.prepared_by }} -->
<!DOCTYPE html></p>

<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333333;
            margin: 0;
            padding: 0;
            background-color: #f9f9f9;
        }
        .container {
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            border: 1px solid #e0e0e0;
        }
        .header {
            background-color: #fcfcfc;
            padding: 25px;
            border-bottom: 3px solid #D62828;
            text-align: center;
        }
        .content {
            padding: 30px;
        }
        .highlight-box {
            background-color: #fff5f5;
            border-left: 4px solid #D62828;
            padding: 15px;
            margin: 20px 0;
            font-style: italic;
        }
        .button-container {
            text-align: center;
            margin: 35px 0;
        }
        .btn {
            background-color: #D62828;
            color: #ffffff !important;
            padding: 14px 35px;
            text-decoration: none;
            font-size: 16px;
            font-weight: 600;
            border-radius: 5px;
            display: inline-block;
        }
        .footer {
            padding: 20px;
            background-color: #f1f1f1;
            font-size: 12px;
            color: #777777;
            text-align: center;
        }
        p {
            margin-bottom: 15px;
        }
        strong {
            color: #1a1a1a;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header Section -->
        <div class="header">
            <h2 style="margin:0; color: #D62828; font-size: 20px;">Review Required: Cost Estimation Sheet</h2>
        </div>


<pre><code>    &lt;!-- Main Body Section --&gt;
    &lt;div class="content"&gt;
        &lt;p&gt;Dear 
            {% if doc.recipient_name %}
                {{ doc.recipient_name }}
            {% else %}
                Sir/Madam
            {% endif %},
        &lt;/p&gt;

        &lt;p&gt;
            The &lt;strong&gt;Cost Estimation Sheet ({{ doc.tech_pack_no or doc.name or "New Document" }})&lt;/strong&gt; 
            has been finalized and is now ready for your professional review and approval.
        &lt;/p&gt;

        &lt;div class="highlight-box"&gt;
            As this document directly impacts &lt;strong&gt;pricing, margin, and production planning&lt;/strong&gt;, 
            your validation is critical before we proceed to the next stage of execution.
        &lt;/div&gt;

        &lt;p&gt;
            Kindly prioritize this request to ensure there are no delays in our production timeline. 
            You can access the document directly via the link below:
        &lt;/p&gt;

        &lt;!-- Call to Action Button --&gt;
        &lt;div class="button-container"&gt;
            {% set form_url = frappe.utils.get_url_to_form(doc.doctype, doc.name) %}
            {% if form_url %}
                &lt;a href="{{ form_url }}" class="btn"&gt;
                    CLICK HERE TO REVIEW &amp; APPROVE
                &lt;/a&gt;
            {% else %}
                &lt;p style="color: #D62828;"&gt;&lt;em&gt;(Link unavailable, please log in to the system to review)&lt;/em&gt;&lt;/p&gt;
            {% endif %}
        &lt;/div&gt;

        &lt;p&gt;Thank you for your continuous guidance and support.&lt;/p&gt;

        &lt;p style="margin-top: 25px;"&gt;
            Best Regards,&lt;br&gt;
            &lt;strong&gt;The Merchandising Team&lt;/strong&gt;&lt;br&gt;
            &lt;small style="color: #888;"&gt;Prepared by: {{ doc.prepared_by or "ERP System" }}&lt;/small&gt;
        &lt;/p&gt;
    &lt;/div&gt;

    &lt;!-- Footer Section --&gt;
    &lt;div class="footer"&gt;
        This is an automated notification from Frappe ERP System regarding Cost Estimation {{ doc.name }}.
    &lt;/div&gt;
&lt;/div&gt;
</code></pre>


</body>
</html>
