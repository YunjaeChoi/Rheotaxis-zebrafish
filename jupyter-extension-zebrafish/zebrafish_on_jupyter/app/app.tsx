import { ContentRef } from "@nteract/core";
import * as React from "react";
import NteractApp from "./nteract-app";

import {
  ExecuteButton,
  InterruptButton,
  UpdateButton
} from "./components/buttons";

import {
  OutputDisplay
} from "./components/output-display";

import {
  Segment,
  Header,
  Icon,
  Menu,
  Container,
  Divider,
  Modal,
  Button,
  Grid,
  Divider,
  Item,
  Message,
  Dropdown,
  Checkbox
} from 'semantic-ui-react'
import {
  Slider,
  InputNumber,
} from 'antd'
import 'semantic-ui-css/semantic.min.css'
import 'antd/dist/antd.css'
import logo from './logo.svg'

import settings from './app-settings/settings.json';


const TopMenuStyle = {
  borderRadius: 0,
  zIndex: 999999,
};

const detectionOutputTypeList = settings.detectionOutputTypes.list.map(
  (outputType) => {
    return { key: outputType, text: outputType, value: outputType }
  }
);

const detMethodList = settings.detection.methods.list.map(
  (method) => {
    return { key: method, text: method, value: method }
  }
);

const postOutputTypeList = settings.postOutputTypes.list.map(
  (outputType) => {
    return { key: outputType, text: outputType, value: outputType }
  }
);

const postTrackerList = settings.postprocess.trackers.list.map(
  (method) => {
    return { key: method, text: method, value: method }
  }
);

class App extends React.Component<{ contentRef: ContentRef }> {
  state = {
    activeTopMenuItem: 'detection',
    executeCellNum: settings.cellNums.detect,

    //settings
    //detection
    detectionOutputType: settings.detectionOutputTypes.default,
    detMethod: settings.detection.methods.default,
    detCropHeightBound: settings.detection.params.cropHeightBound.default,
    detCropWidthBound: settings.detection.params.cropWidthBound.default,
    detFlow: settings.detection.params.flowLeftToRight.default,

    thdLThreshold: settings.detection.params.ThresholdDetector.lThreshold.default,
    thdSizeBound: settings.detection.params.ThresholdDetector.sizeBound.default,
    thdClosingIterations: settings.detection.params.ThresholdDetector.closingIterations.default,

    //post
    postOutputType: settings.postOutputTypes.default,
    postTracker: settings.postprocess.trackers.default,

    vctFramesToFind: settings.postprocess.params.VicinityTracker.framesTofind.default,
    vctMaxDist: settings.postprocess.params.VicinityTracker.maxDist.default,
    vctMaxDistIncRatio: settings.postprocess.params.VicinityTracker.maxDistIncRatio.default,

    dataConverterSelected: settings.postprocess.params.DataConverter.selected,
    dcnFps: settings.postprocess.params.DataConverter.fps,
    dcnPixelToCmRatio: settings.postprocess.params.DataConverter.pixelToCmRatio,
    dcnPixelDiffToPixelVelocity: settings.postprocess.params.DataConverter.pixelDiffToPixelVelocity,
    dcnPixelToCm: settings.postprocess.params.DataConverter.pixelToCm,
    dcnRelAngleDegToSinRelAngle: settings.postprocess.params.DataConverter.relAngleDegToSinRelAngle,
    dcnRelAngleDegToCosRelAngle: settings.postprocess.params.DataConverter.relAngleDegToCosRelAngle,

    positionBounderSelected: settings.postprocess.params.PositionBounder.selected,
    pbdBounds: settings.postprocess.params.PositionBounder.default,
    pbdXBound: settings.postprocess.params.PositionBounder.xBound.default,
    pbdYBound: settings.postprocess.params.PositionBounder.yBound.default,

  };

  //top menu
  onTopMenuItemClick = (e, { name }) => {
    this.setState({ activeTopMenuItem: name });
    if (name === 'detection'){
      this.setState({ executeCellNum: settings.cellNums.detect });
    }
    else if (name === 'postprocess'){
      this.setState({ executeCellNum: settings.cellNums.post });
    }
  };

  //settings page functions
  updateSettingsSource = () => {
    let detFlow;
    if (this.state.detFlow){
      detFlow = 'True';
    }
    else{
      detFlow = 'False';
    }

    let dcnSel;
    if (this.state.dataConverterSelected){
      dcnSel = 'True';
    }
    else{
      dcnSel = 'False';
    }

    let dcnPDPV, dcnPTC, dcnRADTSRA, dcnRADTCRA;
    if (this.state.dcnPixelDiffToPixelVelocity){
      dcnPDPV = 'True';
    }
    else{
      dcnPDPV = 'False';
    }
    if (this.state.dcnPixelToCm){
      dcnPTC = 'True';
    }
    else{
      dcnPTC = 'False';
    }
    if (this.state.dcnRelAngleDegToSinRelAngle){
      dcnRADTSRA = 'True';
    }
    else{
      dcnRADTSRA = 'False';
    }
    if (this.state.dcnRelAngleDegToCosRelAngle){
      dcnRADTCRA = 'True';
    }
    else{
      dcnRADTCRA = 'False';
    }

    let pbdSel;
    if (this.state.positionBounderSelected){
      pbdSel = 'True';
    }
    else{
      pbdSel = 'False';
    }
    let stringList = [
      `${settings.paramNames.detectionOutputType} = '${this.state.detectionOutputType}'`,

      `${settings.paramNames.detMethod} = '${this.state.detMethod}'`,
      `${settings.paramNames.detCropHeightBound[0]} = ${this.state.detCropHeightBound[0]}`,
      `${settings.paramNames.detCropHeightBound[1]} = ${this.state.detCropHeightBound[1]}`,
      `${settings.paramNames.detCropWidthBound[0]} = ${this.state.detCropWidthBound[0]}`,
      `${settings.paramNames.detCropWidthBound[1]} = ${this.state.detCropWidthBound[1]}`,
      `${settings.paramNames.detFlow} = ${detFlow}`,

      `${settings.paramNames.thdLThreshold} = (${this.state.thdLThreshold})`,
      `${settings.paramNames.thdSizeBound} = (${this.state.thdSizeBound})`,
      `${settings.paramNames.thdClosingIterations} = ${this.state.thdClosingIterations}`,

      `${settings.paramNames.postOutputType} = '${this.state.postOutputType}'`,
      `${settings.paramNames.postTracker} = '${this.state.postTracker}'`,

      `${settings.paramNames.vctFramesToFind} = ${this.state.vctFramesToFind}`,
      `${settings.paramNames.vctMaxDist} = ${this.state.vctMaxDist}`,
      `${settings.paramNames.vctMaxDistIncRatio} = ${this.state.vctMaxDistIncRatio}`,

      `${settings.paramNames.dataConverterSelected} = ${dcnSel}`,
      `${settings.paramNames.dcnFps} = ${this.state.dcnFps}`,
      `${settings.paramNames.dcnPixelToCmRatio} = ${this.state.dcnPixelToCmRatio}`,
      `${settings.paramNames.dcnPixelDiffToPixelVelocity} = ${dcnPDPV}`,
      `${settings.paramNames.dcnPixelToCm} = ${dcnPTC}`,
      `${settings.paramNames.dcnRelAngleDegToSinRelAngle} = ${dcnRADTSRA}`,
      `${settings.paramNames.dcnRelAngleDegToCosRelAngle} = ${dcnRADTCRA}`,

      `${settings.paramNames.positionBounderSelected} = ${pbdSel}`,
      `${settings.paramNames.pbdBounds} = ` + JSON.stringify(this.state.pbdBounds, null, 0),
      "print('Settings saved at:', datetime.datetime.now())"
    ];



    return (stringList.join('\n'))
  };

  onDetectionOutputTypeChange = (e, { value }) => this.setState({ detectionOutputType: value });

  onDetMethodChange = (e, { value }) => this.setState({ detMethod: value });

  onPostOutputTypeChange = (e, { value }) => this.setState({ postOutputType: value });

  onPostTrackerChange = (e, { value }) => this.setState({ postTracker: value });

  onPbdBoundAddClick = () => this.setState(
    {
      pbdBounds: [...this.state.pbdBounds, [this.state.pbdXBound, this.state.pbdYBound]]
    }
  );

  onPbdBoundDelteClick = (index) => {
    let bounds = this.state.pbdBounds.slice();
    if (index >= 0) {
      bounds.splice(index, 1)
      this.setState({pbdBounds: bounds})
    };
  };

  boolChange = (key) => {
    return () => {
      this.setState({
        [key]: !this.state[key],
      })
    }
  };

  inputNumberChange = (key) => {
    return (value) => {
      this.setState({
        [key]: value,
      })
    }
  };

  boundedSliderChange = (key) => {
    return (value) => {
      this.setState({
        [key]: value,
      })
    }
  };

  boundedSliderLeftInputChange = (key) => {
    return (value) => {
      let sv = this.state[key].slice();
      sv[0] = value;
      this.setState({
        [key]: sv,
      })
    }
  };

  boundedSliderRightInputChange = (key) => {
    return (value) => {
      let sv = this.state[key].slice();
      sv[1] = value;
      this.setState({
        [key]: sv,
      })
    }
  };

  //initializations

  loadApp = () => {
    //notebook first, wait 1 second and detection
    this.setState(
      { activeTopMenuItem: 'notebook' },
      () => {
        setTimeout(
          () => {
            this.setState({ activeTopMenuItem: 'detection' });
          },
          1000
        );
      }
    );
  };

  getPage = () => {
    let page;
    //if notebook or not
    if (this.state.activeTopMenuItem === 'notebook'){
      page = (
        <React.Fragment>
          <NteractApp contentRef={this.props.contentRef}/>
        </React.Fragment>
      );
    }
    else {
      //select from top menu
      let executionSegment = (
        <Segment.Group>
          <Segment>
            <Divider horizontal>
              <Header as='h3'>Initialize</Header>
            </Divider>
            <Message info>
              <Message.Header>Initialize before configuring settings or processing.</Message.Header>
            </Message>
            <ExecuteButton
              contentRef={this.props.contentRef}
              cellToExecute={settings.cellNums.initialize}
              content='Initialize'
              primary={true}
              fluid={true}
            />
            <OutputDisplay
              contentRef={this.props.contentRef}
              cellToDisplay={settings.cellNums.initialize}
              expanded={false}
              hidden={false}
            />
          </Segment>

          <Segment>
            <Divider horizontal>
              <Header as='h3'>
                <Icon name='file video' />
                <Icon name='file excel' />
                <Header.Content>
                  Files
                </Header.Content>
              </Header>
            </Divider>
            <Grid columns={2}>
              <Grid.Column>
                <Message info>
                  <Message.Header>Files to process should be in 'data/'.</Message.Header>
                </Message>
              </Grid.Column>
              <Grid.Column>
                <ExecuteButton
                  contentRef={this.props.contentRef}
                  cellToExecute={settings.cellNums.updateFiles}
                  content='Get Current Files'
                  primary={false}
                  fluid={true}
                />
              </Grid.Column>
            </Grid>
            <OutputDisplay
              contentRef={this.props.contentRef}
              cellToDisplay={settings.cellNums.updateFiles}
              expanded={false}
              hidden={false}
            />
          </Segment>

          <Segment>
            <Divider horizontal>
              <Header as='h3'>Detection Preview</Header>
            </Divider>
            <Modal size={'large'} trigger={<Button positive fluid>Show Preview</Button>}>
              <Modal.Header>Detection Preview</Modal.Header>
              <Modal.Content scrolling>
                <Modal.Description>
                  <ExecuteButton
                    contentRef={this.props.contentRef}
                    cellToExecute={settings.cellNums.previewDetection}
                    content='Get Preview'
                    primary={true}
                    fluid={true}
                  />
                  <OutputDisplay
                    contentRef={this.props.contentRef}
                    cellToDisplay={settings.cellNums.previewDetection}
                    expanded={true}
                    hidden={false}
                  />
                </Modal.Description>
              </Modal.Content>
            </Modal>
          </Segment>
          <Segment>
            <Divider horizontal>
              <Header as='h3'>Processing</Header>
            </Divider>
            <Grid columns={2}>
              <Grid.Column>
                <ExecuteButton
                  contentRef={this.props.contentRef}
                  cellToExecute={this.state.executeCellNum}
                  content='Run'
                  primary={true}
                  fluid={true}
                />
              </Grid.Column>
              <Grid.Column>
                <InterruptButton
                  contentRef={this.props.contentRef}
                  content='Interrupt'
                  negative={true}
                  fluid={true}
                />
              </Grid.Column>
            </Grid>
            <OutputDisplay
              contentRef={this.props.contentRef}
              cellToDisplay={this.state.executeCellNum}
              expanded={true}
              hidden={false}
            />
          </Segment>
        </Segment.Group>
      );

      //settings
      let settingsFragment;
      let settingsHeader, settingsBody, settingsFooter;

      if (this.state.activeTopMenuItem === 'detection'){
        settingsHeader = (
          <React.Fragment>
            <Segment.Group horizontal>
              <Segment>
                <Header as='h4'>
                  Output Type
                  <Header.Subheader>
                    Select output type
                  </Header.Subheader>
                </Header>
              </Segment>
              <Segment>
                <Dropdown
                  onChange={this.onDetectionOutputTypeChange}
                  options={detectionOutputTypeList}
                  placeholder='Select a method'
                  selection
                  fluid
                  value={this.state.detectionOutputType}
                />
              </Segment>
            </Segment.Group>
            <Segment.Group horizontal>
              <Segment>
                <Header as='h4'>
                  Detection Method
                  <Header.Subheader>
                    Select a method
                  </Header.Subheader>
                </Header>
              </Segment>
              <Segment>
                <Dropdown
                  onChange={this.onDetMethodChange}
                  options={detMethodList}
                  placeholder='Select a method'
                  selection
                  fluid
                  value={this.state.detMethod}
                />
              </Segment>
            </Segment.Group>
          </React.Fragment>
        );

        if (this.state.detMethod === 'ThresholdDetector'){
          settingsBody = (
            <Segment.Group>
              <Segment>
                <Divider horizontal>
                  <Header as='h4'>Image Crop</Header>
                </Divider>

                <Header as='h4' dividing>Height bound</Header>
                <Grid container>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.detCropHeightBound[0]}
                      onChange={this.boundedSliderLeftInputChange('detCropHeightBound')}
                    />
                  </Grid.Column>
                  <Grid.Column width={10}>
                    <Slider
                      range
                      min={settings.detection.params.cropHeightBound.min}
                      max={settings.detection.params.cropHeightBound.max}
                      step={1}
                      defaultValue={this.state.detCropHeightBound}
                      value={this.state.detCropHeightBound}
                      onChange={this.boundedSliderChange('detCropHeightBound')}
                    />
                  </Grid.Column>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.detCropHeightBound[1]}
                      onChange={this.boundedSliderRightInputChange('detCropHeightBound')}
                    />
                  </Grid.Column>
                </Grid>

                <Header as='h4' dividing>Width bound</Header>
                <Grid container>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.detCropWidthBound[0]}
                      onChange={this.boundedSliderLeftInputChange('detCropWidthBound')}
                    />
                  </Grid.Column>
                  <Grid.Column width={10}>
                    <Slider
                      range
                      min={settings.detection.params.cropWidthBound.min}
                      max={settings.detection.params.cropWidthBound.max}
                      step={1}
                      defaultValue={this.state.detCropWidthBound}
                      value={this.state.detCropWidthBound}
                      onChange={this.boundedSliderChange('detCropWidthBound')}
                    />
                  </Grid.Column>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.detCropWidthBound[1]}
                      onChange={this.boundedSliderRightInputChange('detCropWidthBound')}
                    />
                  </Grid.Column>
                </Grid>
              </Segment>

              <Segment>
                <Divider horizontal><Header as='h4'>Flow</Header></Divider>
                <Checkbox
                  label='Check if water flows left to right'
                  onChange={this.boolChange('detFlow')}
                  checked={this.state.detFlow}
                />
              </Segment>

              <Segment>
                <Divider horizontal><Header as='h4'>Thresholds</Header></Divider>
                <Header as='h4' dividing>L Channel Threshold</Header>
                <Grid container>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.thdLThreshold[0]}
                      onChange={this.boundedSliderLeftInputChange('thdLThreshold')}
                    />
                  </Grid.Column>
                  <Grid.Column width={10}>
                    <Slider
                      range
                      min={settings.detection.params.ThresholdDetector.lThreshold.min}
                      max={settings.detection.params.ThresholdDetector.lThreshold.max}
                      step={1}
                      defaultValue={this.state.thdLThreshold}
                      value={this.state.thdLThreshold}
                      onChange={this.boundedSliderChange('thdLThreshold')}
                    />
                  </Grid.Column>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.thdLThreshold[1]}
                      onChange={this.boundedSliderRightInputChange('thdLThreshold')}
                    />
                  </Grid.Column>
                </Grid>
                <Header as='h4' dividing>Size bound</Header>
                <Grid container>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.thdSizeBound[0]}
                      onChange={this.boundedSliderLeftInputChange('thdSizeBound')}
                    />
                  </Grid.Column>
                  <Grid.Column width={10}>
                    <Slider
                      range
                      min={settings.detection.params.ThresholdDetector.sizeBound.min}
                      max={settings.detection.params.ThresholdDetector.sizeBound.max}
                      step={1}
                      defaultValue={this.state.thdSizeBound}
                      value={this.state.thdSizeBound}
                      onChange={this.boundedSliderChange('thdSizeBound')}
                    />
                  </Grid.Column>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.thdSizeBound[1]}
                      onChange={this.boundedSliderRightInputChange('thdSizeBound')}
                    />
                  </Grid.Column>
                </Grid>
                <Header as='h4' dividing>Closing iterations</Header>
                <InputNumber
                  min={settings.detection.params.ThresholdDetector.closingIterations.min}
                  max={settings.detection.params.ThresholdDetector.closingIterations.max}
                  defaultValue={this.state.thdClosingIterations}
                  onChange={this.inputNumberChange('thdClosingIterations')}
                />
              </Segment>
            </Segment.Group>
          );
        }
      }
      else if (this.state.activeTopMenuItem === 'postprocess'){
        settingsHeader = (
          <React.Fragment>
            <Segment.Group horizontal>
              <Segment>
                <Header as='h4'>
                  Output Type
                  <Header.Subheader>
                    Select output type
                  </Header.Subheader>
                </Header>
              </Segment>
              <Segment>
                <Dropdown
                  onChange={this.onPostOutputTypeChange}
                  options={postOutputTypeList}
                  placeholder='Select a method'
                  selection
                  fluid
                  value={this.state.postOutputType}
                />
              </Segment>
            </Segment.Group>
            <Segment.Group horizontal>
              <Segment>
                <Header as='h4'>
                  Tracker
                  <Header.Subheader>
                    Select a tracker
                  </Header.Subheader>
                </Header>
              </Segment>
              <Segment>
                <Dropdown
                  onChange={this.onPostTrackerChange}
                  options={postTrackerList}
                  placeholder='Select a tracker'
                  selection
                  fluid
                  value={this.state.postTracker}
                />
              </Segment>
            </Segment.Group>
          </React.Fragment>
        );

        let trackerSettings;
        if (this.state.postTracker === 'VicinityTracker'){
          trackerSettings = (
            <React.Fragment>
              <Segment.Group>
                <Segment>
                  <Header as='h4' dividing>Number of frames to find</Header>
                  <InputNumber
                    min={0}
                    value={this.state.vctFramesToFind}
                    onChange={this.inputNumberChange('vctFramesToFind')}
                  />
                </Segment>
                <Segment>
                  <Header as='h4' dividing>Max distance to find</Header>
                  <InputNumber
                    min={0}
                    value={this.state.vctMaxDist}
                    onChange={this.inputNumberChange('vctMaxDist')}
                  />
                </Segment>
                <Segment>
                  <Header as='h4' dividing>Max distance increment ratio per frame</Header>
                  <InputNumber
                    min={0}
                    value={this.state.vctMaxDistIncRatio}
                    step={0.01}
                    onChange={this.inputNumberChange('vctMaxDistIncRatio')}
                  />
                </Segment>
              </Segment.Group>
            </React.Fragment>
          );
        };

        let dataConverterSettings, positionBounderSettings;
        if (this.state.dataConverterSelected){
          dataConverterSettings = (
            <Segment>
              <Header as='h4' dividing>Frames per second</Header>
              <InputNumber
                min={0}
                value={this.state.dcnFps}
                onChange={this.inputNumberChange('dcnFps')}
              />
              <Header as='h4' dividing>Pixel to cm ratio</Header>
              <InputNumber
                min={0}
                value={this.state.dcnPixelToCmRatio}
                step={0.0001}
                onChange={this.inputNumberChange('dcnPixelToCmRatio')}
              />
              <Header as='h4' dividing>Select converting methods</Header>
              <Checkbox
                toggle
                label='Convert pixel difference to pixel velocity'
                onChange={this.boolChange('dcnPixelDiffToPixelVelocity')}
                checked={this.state.dcnPixelDiffToPixelVelocity}
              />
              <Header dividing/>
              <Checkbox
                toggle
                label='Convert pixel velocity to velocity(cm/s)'
                onChange={this.boolChange('dcnPixelToCm')}
                checked={this.state.dcnPixelToCm}
              />
              <Header dividing/>
              <Checkbox
                toggle
                label='Convert relative angle to sin(relative angle)'
                onChange={this.boolChange('dcnRelAngleDegToSinRelAngle')}
                checked={this.state.dcnRelAngleDegToSinRelAngle}
              />
              <Header dividing/>
              <Checkbox
                toggle
                label='Convert relative angle to cos(relative angle)'
                onChange={this.boolChange('dcnRelAngleDegToCosRelAngle')}
                checked={this.state.dcnRelAngleDegToCosRelAngle}
              />
            </Segment>
          );
        };
        if (this.state.positionBounderSelected){
          positionBounderSettings = (
            <Segment>
              <Segment>
                <Header as='h4' dividing>x bound</Header>
                <Grid container>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.pbdXBound[0]}
                      onChange={this.boundedSliderLeftInputChange('pbdXBound')}
                    />
                  </Grid.Column>
                  <Grid.Column width={10}>
                    <Slider
                      range
                      min={settings.postprocess.params.PositionBounder.xBound.min}
                      max={settings.postprocess.params.PositionBounder.xBound.max}
                      step={1}
                      defaultValue={this.state.pbdXBound}
                      value={this.state.pbdXBound}
                      onChange={this.boundedSliderChange('pbdXBound')}
                    />
                  </Grid.Column>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.pbdXBound[1]}
                      onChange={this.boundedSliderRightInputChange('pbdXBound')}
                    />
                  </Grid.Column>
                </Grid>
                <Header as='h4' dividing>y bound</Header>
                <Grid container>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.pbdYBound[0]}
                      onChange={this.boundedSliderLeftInputChange('pbdYBound')}
                    />
                  </Grid.Column>
                  <Grid.Column width={10}>
                    <Slider
                      range
                      min={settings.postprocess.params.PositionBounder.yBound.min}
                      max={settings.postprocess.params.PositionBounder.yBound.max}
                      step={1}
                      defaultValue={this.state.pbdYBound}
                      value={this.state.pbdYBound}
                      onChange={this.boundedSliderChange('pbdYBound')}
                    />
                  </Grid.Column>
                  <Grid.Column width={3}>
                    <InputNumber
                      value={this.state.pbdYBound[1]}
                      onChange={this.boundedSliderRightInputChange('pbdYBound')}
                    />
                  </Grid.Column>
                </Grid>
              </Segment>
              <Button primary onClick={this.onPbdBoundAddClick}>Add bound</Button>
              <Header as='h4' dividing>Current Bounds</Header>
              <Item.Group divided>
                {this.state.pbdBounds.map((e, i) =>
                  <Item key={i}>
                    <Item.Content verticalAlign='middle'>
                      x low: {e[0][0]},  x high: {e[0][1]},  y low: {e[1][0]},  y high: {e[1][1]}
                      <Button
                        floated='right'
                        circular icon='delete'
                        size='tiny'
                        onClick={this.onPbdBoundDelteClick.bind(this, i)}
                      />
                    </Item.Content>
                  </Item>
                )}
              </Item.Group>
            </Segment>
          );
        };

        settingsBody = (
          <React.Fragment>
            {trackerSettings}
            <Segment.Group>
              <Segment>
                <Divider horizontal><Header as='h4'>Methods</Header></Divider>
                <Header as='h4' dividing>DataConverter</Header>
                <Checkbox
                  toggle
                  label='Run DataConverter'
                  onChange={this.boolChange('dataConverterSelected')}
                  checked={this.state.dataConverterSelected}
                />
                {dataConverterSettings}
                <Header as='h4' dividing>PositionBounder</Header>
                <Checkbox
                  toggle
                  label='Run PositionBounder'
                  onChange={this.boolChange('positionBounderSelected')}
                  checked={this.state.positionBounderSelected}
                />
                {positionBounderSettings}
              </Segment>
            </Segment.Group>
          </React.Fragment>
        );
      }

      settingsFooter = (
        <React.Fragment>
          <UpdateButton
            contentRef={this.props.contentRef}
            cellToUpdate={settings.cellNums.updateSettings}
            content='Save Settings'
            updateSource={this.updateSettingsSource}
          />
          <OutputDisplay
            contentRef={this.props.contentRef}
            cellToDisplay={settings.cellNums.updateSettings}
            expanded={true}
            hidden={false}
          />
        </React.Fragment>
      );

      settingsFragment = (
        <React.Fragment>
          {settingsHeader}
          {settingsBody}
          {settingsFooter}
        </React.Fragment>
      );


      //page
      page = (
        <React.Fragment>
          <Grid columns={2}>
            <Grid.Column>
              <Segment>
                <Divider horizontal>
                  <Header as='h3'>
                    <Icon name='settings' />
                    Settings
                  </Header>
                </Divider>
                {settingsFragment}
              </Segment>
            </Grid.Column>
            <Grid.Column>
              {executionSegment}
            </Grid.Column>
          </Grid>
        </React.Fragment>
      );
    }
    return page
  };

  componentDidMount() {
    this.loadApp();
  }

  render(): JSX.Element {
    const { activeTopMenuItem } = this.state

    let page = this.getPage();

    return (
      <React.Fragment>
        <Menu fixed='top' style={TopMenuStyle} pointing inverted>
          <Menu.Item header as='h3'>
            <img src={logo} className="App-logo" alt="logo" />
            Zebrafish
          </Menu.Item>
          <Menu.Item
            name='detection'
            active={activeTopMenuItem === 'detection'}
            onClick={this.onTopMenuItemClick}
            header
            as='h4'
          >
            Detection
          </Menu.Item>

          <Menu.Item
            name='postprocess'
            active={activeTopMenuItem === 'postprocess'}
            onClick={this.onTopMenuItemClick}
            header
            as='h4'
          >
            Postprocess
          </Menu.Item>

          <Menu.Menu position='right'>
            <Menu.Item name='notebook'
              active={activeTopMenuItem === 'notebook'}
              onClick={this.onTopMenuItemClick}
              header
              as='h4'
            >
              Notebook
            </Menu.Item>
          </Menu.Menu>
        </Menu>
        <Segment basic size='small'/>
        {page}
      </React.Fragment>
    );
  }
}

export default App;
