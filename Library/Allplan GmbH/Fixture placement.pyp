<?xml version="1.0" encoding="utf-8"?>
<Element xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:noNamespaceSchemaLocation="https://pythonparts.allplan.com/2026/schemas/PythonPart.xsd">
  <Script>
    <Name>allplan_gmbh\fixture_placement.py</Name>
    <Title>FixturePlacement</Title>
    <Version>0.2</Version>
    <Interactor>True</Interactor>
    <ReadLastInput>False</ReadLastInput>
  </Script>
  <Page>
    <Name>FixtureSelectionPage</Name>
    <Text>Fixture selection</Text>
    <Parameters>

      <Parameter>
        <Name>FixtureSelectionExpander</Name>
        <Text>Fixture selection</Text>
        <ValueType>Expander</ValueType>
        <Visible>SelectedPath == ""</Visible>
        <Parameters>
          <Parameter>
            <Name>VsPyPSelectButtonRow</Name>
            <Text>Select fixture .pyp file</Text>
            <ValueType>Row</ValueType>

            <Parameters>
              <Parameter>
                <Name>VsPyPSelectButton</Name>
                <Text>Browse ...</Text>
                <EventId>1000</EventId>
                <ValueType>Button</ValueType>
                <Enable>SelectedPath == ""</Enable>
              </Parameter>
            </Parameters>
          </Parameter>

          <Parameter>
            <Name>SnapByRadioGroup</Name>
            <Text>Snap by</Text>
            <Value>SnapByRay</Value>
            <ValueType>RadioButtonGroup</ValueType>
            <Parameters>
              <Parameter>
                <Name>SnapByRay</Name>
                <Text>ray</Text>
                <Value>SnapByRay</Value>
                <ValueType>RadioButton</ValueType>
              </Parameter>
              <Parameter>
                <Name>SnapByPoint</Name>
                <Text>point</Text>
                <Value>SnapByPoint</Value>
                <ValueType>RadioButton</ValueType>
              </Parameter>
            </Parameters>
          </Parameter>
        </Parameters>
      </Parameter>
    </Parameters>
  </Page>
  <Page>
    <Name>__HiddenPage__</Name>
    <Text></Text>
    <Parameters>
      <Parameter>
        <Name>SelectedPath</Name>
        <Text></Text>
        <Value />
        <ValueType>String</ValueType>
      </Parameter>
    </Parameters>
  </Page>
</Element>