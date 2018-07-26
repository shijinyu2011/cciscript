daily_template = '''
<html>
    <head>
       <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
      <script src="http://code.highcharts.com/highcharts.js"></script>
    </head>

<body>
<div id="container" style="height: 300px"></div>
<div id="container_detail" style="height: 300px"></div>
</body>
<script type="text/javascript">
$(function () {
    $('#container').highcharts({
        chart: {
            type: 'spline'
        },
        title: {
            text: '%(project)s Weekly report(%(start_date)s ~ %(end_date)s)'
        },
        xAxis: {
            categories: %(xaxis)s
        },
        yAxis: {
            min: 0,
            max: 100,            
            tickInterval: 10,
            title: {
                text: 'Usage rate'
            }
        },
        series: %(yaxis)s
      });
    });
$(function () {
    $('#container_detail').highcharts({
        chart: {
            type: 'area'
        },

        title: {
            text: 'Project <%(project)s> usage details'
        },

        xAxis: {
            type: 'datetime'
        },

        yAxis: {
            title: {
                text: null
            }
        },
        series: [{
            name: 'Instance',
            data: %(instance_details)s,
            zIndex: 1,
        }, {
            name: 'Connection',
            data: %(connection_details)s,
            zIndex: 0
        }]
    });
});
</script>
</html>
'''