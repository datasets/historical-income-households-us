import datetime

from dataflows import Flow, PackageWrapper, ResourceWrapper, validate
from dataflows import add_metadata, dump_to_path, load, set_type, find_replace, printer


def rename(package: PackageWrapper):
    package.pkg.descriptor['resources'][0]['name'] = 'household-income-us-historical'
    package.pkg.descriptor['resources'][0]['path'] = 'data/household-income-us-historical.csv'
    yield package.pkg
    res_iter = iter(package)
    first: ResourceWrapper = next(res_iter)
    yield first.it
    yield from package


household_us = Flow(
    add_metadata(
        name="household-income-us-historical",
        title="Income Limits for Each Fifth and Top 5 Percent of All Households:  1967 to 2016",
        description="Households as of March of the following year. Income in current and 2016 CPI-U-RS adjusted dollars.",
        sources=[
            {
              "path": "https://www2.census.gov",
              "title": "United States Census Bureau"
            }
        ],
        licenses="PDDL-1.0",
        version="0.3.0",
        views=[
            {
                "name": "comparison-of-upper-limit-of-each-fifth-and-lower-limit-of-top-5-percent",
                "title": "Comparison of upper limit of each fifth and lower limit of top 5 percent (2016 dollars)",
                "resources": ["household-income-us-historical"],
                "specType": "simple",
                "spec": {
                    "type": "line",
                    "group": "Year",
                    "series": ["Lowest", "Second", "Third", "Fourth", "Top 5 percent"]
                }
            },
            {
                "name": "lowest-fifth-vs-top-5-percent",
                "title": "Ratio of lower limit of top 5 percent to upper limit of lowest fifth (2016 dollars)",
                "resources": [
                    {
                        "name": "household-income-us-historical",
                        "transform": [
                            {
                                "type": "formula",
                                "expressions": ["data['Top 5 percent']/data['Lowest']"],
                                "asFields": ["Ratio"]
                            }
                        ]
                    }
                ],
                "specType": "simple",
                "spec": {"type": "line","group": "Year","series": ["Ratio"]}
            }
        ]
    ),
    load(
        load_source='https://www2.census.gov/programs-surveys/cps/tables/time-series/historical-income-households/h01ar.xls',
        format='xls',
        sheet= 1,
        # remove first 6 rows. remove rows that contain data from 1967 - last year and 3 rows after. Finaly last row
        skip_rows=[i+1 for i in range(6 + datetime.datetime.now().year - 1966 + 3)] + [-1],
        headers=['Year', 'Number (thousands)', 'Lowest', 'Second', 'Third', 'Fourth', 'Top 5 percent']
    ),
    find_replace(fields=[
        {
            'name': 'Year', 'patterns': [
                {'find': '(\s?\(\d+\))|(\.0)', 'replace': ''}
            ]
        },
        {
            'name': 'Fourth', 'patterns': [
                {'find': '\+|', 'replace': ''}
            ]
        }
    ], resources='un-countries'),
    set_type('Year', type='year'),
    set_type('Number (thousands)', type='number'),
    set_type('Lowest', type='number'),
    set_type('Second', type='number'),
    set_type('Third', type='number'),
    set_type('Fourth', type='number'),
    set_type('Top 5 percent', type='number'),
    rename,
    validate(),
    printer(),
    dump_to_path(),
)


if __name__ == '__main__':
    household_us.process()
