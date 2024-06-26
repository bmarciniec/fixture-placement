<?xml version="1.0" encoding="utf-8"?>
<Element>
    <Script>
        <Name>FixturePlacement.py</Name>
        <Title>FixturePlacement</Title>
        <Version>0.2</Version>
        <Interactor>True</Interactor>
        <ReadLastInput>False</ReadLastInput>
    </Script>
    <Page>
        <Name>FixtureSelectionPage</Name>
        <Text>Fixture selection</Text>

        <Parameter>
            <Name>FixtureSelectionExpander</Name>
            <Text>Fixture selection</Text>
            <ValueType>Expander</ValueType>
            <Visible>True</Visible>

            <Parameter>
                <Name>FixtureFilePath</Name>
                <Text>Select fixture .pyp file</Text>
                <Value></Value>
                <ValueType>String</ValueType>
                <ValueDialog>OpenFileDialog</ValueDialog>
                <FileFilter>pyp-files(*.pyp)|*.pyp|</FileFilter>
                <FileExtension>pyp</FileExtension>
                <DefaultDirectories>std|usr|prj</DefaultDirectories>
            </Parameter>
            <Parameter>
                <Name>SnapByRadioGroup</Name>
                <Text>Snap by</Text>
                <Value>SnapByRay</Value>
                <ValueType>RadioButtonGroup</ValueType>

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
            </Parameter>
            <Parameter>
                <Name>CreateNiche</Name>
                <Text>Create niche</Text>
                <Value>False</Value>
                <ValueType>CheckBox</ValueType>
            </Parameter>
            <Parameter>
                <Name>OpeningWidth</Name>
                <Text>Width</Text>
                <Value>200</Value>
                <ValueType>Length</ValueType>
                <Visible>CreateNiche</Visible>
            </Parameter>
            <Parameter>
                <Name>OpeningHeight</Name>
                <Text>Height</Text>
                <Value>200</Value>
                <ValueType>Length</ValueType>
                <Visible>CreateNiche</Visible>
            </Parameter>
            <Parameter>
                <Name>OpeningDepth</Name>
                <Text>Depth</Text>
                <Value>50</Value>
                <ValueType>Length</ValueType>
                <Visible>CreateNiche</Visible>
            </Parameter>
        </Parameter>
    </Page>
</Element>
